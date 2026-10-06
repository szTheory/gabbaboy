#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); } while (0)

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

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    printf("1..1\n");
    if (strcmp(argv[1], "wram_guest") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x42,0x77,0x7E};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 56, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 56);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0x42);
        gbb_trace_record trace[8];
        r = gbb_run(m, 8, trace, 8);
        REQUIRE(r.consumed_half_dots == 0);
        gbb_destroy(m);
        PASS("bus_wram_guest");
        return 0;
    }
    if (strcmp(argv[1], "echo_hram") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x91,0x77,0x21,0x00,0xE0,0x7E};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 80, NULL, 0);
        REQUIRE(r.consumed_half_dots == 80);
        REQUIRE(gbb_peek_ram(m, 0xE000) == 0x91);
        gbb_destroy(m);
        const uint8_t hram[] = {0x21,0x80,0xFF,0x3E,0x37,0x77,0x7E};
        m = load_program(hram, sizeof(hram));
        REQUIRE(m != NULL);
        r = gbb_run(m, 56, NULL, 0);
        REQUIRE(r.consumed_half_dots == 56);
        REQUIRE(gbb_peek_ram(m, 0xFF80) == 0x37);
        gbb_destroy(m);
        PASS("bus_echo_hram");
        return 0;
    }
    if (strcmp(argv[1], "absent_cart") == 0) {
        const uint8_t read_program[] = {0x21,0x00,0xA0,0x7E};
        gbb_instance *m = load_program(read_program, sizeof(read_program));
        REQUIRE(m != NULL);
        gbb_trace_record trace[4];
        gbb_run_result r = gbb_run(m, 32, trace, 4);
        REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS && r.consumed_half_dots == 24);
        REQUIRE(r.trace_count == 1 && trace[0].pc == 0x0100);
        gbb_destroy(m);
        const uint8_t write_program[] = {0x21,0x00,0xA0,0x3E,0x55,0x77};
        m = load_program(write_program, sizeof(write_program));
        REQUIRE(m != NULL);
        r = gbb_run(m, 48, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 48);
        REQUIRE(gbb_peek_ram(m, 0xA000) == 0xFF);
        gbb_destroy(m);
        PASS("bus_absent_cart");
        return 0;
    }
    if (strcmp(argv[1], "preflight") == 0) {
        const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x42,0x77};
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_trace_record trace[3];
        memset(trace, 0xA5, sizeof(trace));
        gbb_run_result short_run = gbb_run(m, 23, trace, 3);
        REQUIRE(short_run.reason == GBB_STOP_BUDGET && short_run.consumed_half_dots == 0);
        REQUIRE(short_run.trace_count == 0 && trace[0].pc == 0xA5A5);
        gbb_run_result exact = gbb_run(m, 24, trace, 3);
        REQUIRE(exact.consumed_half_dots == 24 && exact.trace_count == 1);
        REQUIRE(trace[0].pc == 0x0100 && trace[0].time_half_dots == 0);
        gbb_destroy(m);
        PASS("bus_preflight");
        return 0;
    }
    return 2;
}
