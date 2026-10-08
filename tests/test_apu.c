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
        0x3E,0xA3,0xE0,0x17, 0x3E,0xC0,0xE0,0x19,
        0xF0,0x16,0xEA,0x00,0xC0, 0xF0,0x17,0xEA,0x01,0xC0,
        0xF0,0x19,0xEA,0x02,0xC0, 0xF0,0x26,0xEA,0x03,0xC0,
        0x3E,0x00,0xE0,0x17, 0xF0,0x26,0xEA,0x04,0xC0, 0x18,0xFE
    };
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    gbb_run_result r = gbb_run(m, 512u, NULL, 0u);
    int ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC000u) == 0xFFu &&
             gbb_peek_ram(m, 0xC001u) == 0xA3u &&
             gbb_peek_ram(m, 0xC002u) == 0xFFu &&
             gbb_peek_ram(m, 0xC003u) == 0xF2u &&
             gbb_peek_ram(m, 0xC004u) == 0xF0u;
    if (!ok) fprintf(stderr, "reason=%d c000=%02x c001=%02x c002=%02x\n", r.reason,
                     gbb_peek_ram(m, 0xC000u), gbb_peek_ram(m, 0xC001u),
                     gbb_peek_ram(m, 0xC002u));
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int mixer_route(uint8_t routing, int expect_left) {
    uint8_t program[] = {
        0x3E,0x80,0xE0,0x26, 0x3E,0x77,0xE0,0x24,
        0x3E,0x00,0xE0,0x25, 0x3E,0x80,0xE0,0x16,
        0x3E,0xF0,0xE0,0x17, 0x3E,0x00,0xE0,0x18,
        0x3E,0x87,0xE0,0x19, 0x18,0xFE
    };
    program[9] = routing;
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    gbb_audio_frame frames[804] = {{0}};
    size_t count = 0u;
    gbb_run_result r = gbb_run_audio(m, 140448u, frames, 804u, &count);
    int active = 0, inactive = 0;
    if (r.reason == GBB_STOP_BUDGET && count == 803u) {
        for (size_t i = 100u; i < count; ++i) {
            if (expect_left) { active |= frames[i].left != 0; inactive |= frames[i].right != 0; }
            else { active |= frames[i].right != 0; inactive |= frames[i].left != 0; }
        }
    }
    gbb_destroy(m);
    return active && !inactive ? 0 : 1;
}

static int mixer_channels(void) {
    return mixer_route(0x02u, 0) || mixer_route(0x20u, 1);
}

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "apu_pulse";
    printf("TAP version 13\n1..1\n");
    if (strcmp(name, "apu_pulse") == 0) {
        if (pulse_two_registers() != 0) { printf("not ok 1 - apu_pulse\n"); return 1; }
        printf("ok 1 - apu_pulse\n"); return 0;
    }
    if (strcmp(name, "apu_mixer") == 0) {
        if (mixer_channels() != 0) { printf("not ok 1 - apu_mixer\n"); return 1; }
        printf("ok 1 - apu_mixer\n"); return 0;
    }
    printf("not ok 1 - %s # case not implemented yet\n", name);
    return 1;
}
