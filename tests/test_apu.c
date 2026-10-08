#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

static gbb_instance *machine_with_program(const uint8_t *program, size_t size) {
    uint8_t *rom = calloc(1u, 32768u);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100u, program, size);
    checksum(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768u) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static int pulse_two_registers(void) {
    /* NR21, NR22, NR23 and NR24, then read the readable fields back. */
    static const uint8_t program[] = {
        0x3E,0x80,0xE0,0x26, 0x3E,0xC0,0xE0,0x16,
        0x3E,0xA3,0xE0,0x17, 0x3E,0x40,0xE0,0x19,
        0xF0,0x16,0xEA,0x00,0xC0, 0xF0,0x17,0xEA,0x01,0xC0,
        0xF0,0x19,0xEA,0x02,0xC0, 0x18,0xFE
    };
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    gbb_run_result r = gbb_run(m, 512u, NULL, 0u);
    int ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC000u) == 0xFFu &&
             gbb_peek_ram(m, 0xC001u) == 0xA3u &&
             gbb_peek_ram(m, 0xC002u) == 0xFFu;
    gbb_destroy(m);
    return ok ? 0 : 1;
}

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "apu_pulse";
    printf("TAP version 13\n1..1\n");
    if (strcmp(name, "apu_pulse") == 0) {
        if (pulse_two_registers() != 0) { printf("not ok 1 - apu_pulse\n"); return 1; }
        printf("ok 1 - apu_pulse\n"); return 0;
    }
    printf("not ok 1 - %s # case not implemented yet\n", name);
    return 1;
}
