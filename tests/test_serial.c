#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fflush(stdout); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); return 0; } while (0)

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
        gbb_destroy(machine); machine = NULL;
    }
    free(rom);
    return machine;
}

static gbb_instance *load_long_program(const uint8_t *program, size_t length, size_t prefix) {
    uint8_t *rom = calloc(1, 32768);
    if (rom == NULL || prefix > length) { free(rom); return NULL; }
    memcpy(rom + 0x100, program, prefix);
    rom[0x100 + prefix] = 0xC3; rom[0x101 + prefix] = 0x50; rom[0x102 + prefix] = 0x01;
    memcpy(rom + 0x150, program + prefix, length - prefix);
    fix_checksum(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768) != GBB_OK) { gbb_destroy(machine); machine = NULL; }
    free(rom);
    return machine;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    printf("1..1\n");
    if (strcmp(argv[1], "internal_disconnected") == 0 || strcmp(argv[1], "external_pending") == 0) {
        int internal = strcmp(argv[1], "internal_disconnected") == 0;
        uint8_t program[1600] = {0x3E,0x00,0xE0,0x01, 0x3E,0x80};
        size_t used = 6;
        if (internal) program[5] = 0x81;
        program[used++] = 0xE0; program[used++] = 0x02;
        size_t prefix = used;
        for (unsigned i = 0; i < 1300; ++i) program[used++] = 0x00;
        const uint8_t tail[] = {0xF0,0x01,0xEA,0x00,0xC0, 0xF0,0x02,0xEA,0x01,0xC0,
                                0xF0,0x0F,0xEA,0x02,0xC0};
        memcpy(program + used, tail, sizeof(tail)); used += sizeof(tail);
        gbb_instance *m = load_long_program(program, used, prefix); REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 12000, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 12000);
        if (internal) {
            REQUIRE(gbb_peek_ram(m,0xC000) == 0xFF);
            REQUIRE((gbb_peek_ram(m,0xC001) & 0x80u) == 0);
            REQUIRE((gbb_peek_ram(m,0xC002) & 0x08u) != 0);
        } else {
            REQUIRE((gbb_peek_ram(m,0xC001) & 0x80u) != 0);
            REQUIRE((gbb_peek_ram(m,0xC002) & 0x08u) == 0);
        }
        gbb_destroy(m);
        PASS(internal ? "serial_internal_disconnected" : "serial_external_pending");
    }
    if (strcmp(argv[1], "unqualified_overlap") == 0) {
        const uint8_t program[] = {0x3E,0x00,0xE0,0x01, 0x3E,0x81,0xE0,0x02,
                                   0x3E,0x55,0xE0,0x01};
        gbb_instance *m = load_program(program, sizeof(program)); REQUIRE(m != NULL);
        gbb_run_result r = gbb_run(m, 120, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_BUS);
        REQUIRE(r.consumed_half_dots <= 120);
        gbb_destroy(m);
        PASS("serial_unqualified_overlap");
    }
    return 2;
}
