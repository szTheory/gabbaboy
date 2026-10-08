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

static gbb_instance *machine_with_delayed_program(const uint8_t *program, size_t size,
                                                   unsigned delay_nops) {
    uint8_t *rom = calloc(1u, 32768u);
    if (rom == NULL || size > 32768u - 0x150u - delay_nops) { free(rom); return NULL; }
    rom[0x100] = 0xC3u; rom[0x101] = 0x50u; rom[0x102] = 0x01u;
    memcpy(rom + 0x150u + delay_nops, program, size);
    checksum(rom);
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK ||
        gbb_load_rom(m, rom, 32768u) != GBB_OK) { gbb_destroy(m); m = NULL; }
    free(rom);
    return m;
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

static int sequencer_div_write(void) {
    static const uint8_t setup[] = {
        0x3E,0x80,0xE0,0x26, 0x3E,0x3F,0xE0,0x16,
        0x3E,0xF0,0xE0,0x17, 0x3E,0xC0,0xE0,0x19,
        0xF0,0x26,0xEA,0x00,0xC0, 0xAF,0xE0,0x04, 0xF0,0x26,0xEA,0x01,0xC0,
        0x18,0xFE
    };
    gbb_instance *m = machine_with_delayed_program(setup, sizeof(setup), 315u);
    if (m == NULL) return 1;
    gbb_run_result r = gbb_run(m, 4000u, NULL, 0u);
    int ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC000u) == 0xF2u &&
             gbb_peek_ram(m, 0xC001u) == 0xF0u;
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int timeline_partition(void) {
    static const uint8_t program[] = {
        0x3E,0x77,0xE0,0x25, 0x3E,0x3F,0xE0,0x16,
        0x3E,0xF0,0xE0,0x17, 0x3E,0x00,0xE0,0x18,
        0x3E,0xC0,0xE0,0x19, 0x18,0xFE
    };
    gbb_instance *whole = machine_with_program(program, sizeof(program));
    gbb_instance *split = machine_with_program(program, sizeof(program));
    if (whole == NULL || split == NULL) { gbb_destroy(whole); gbb_destroy(split); return 1; }
    gbb_audio_frame a[512] = {{0}}, b[512] = {{0}};
    size_t ac = 0u, bc = 0u;
    gbb_run_result ar = gbb_run_audio(whole, 65536u, a, 512u, &ac);
    int ok = ar.reason == GBB_STOP_BUDGET && ar.consumed_half_dots != 0u;
    const uint64_t target_elapsed = ar.consumed_half_dots;
    uint64_t elapsed = 0u;
    while (ok && elapsed < target_elapsed) {
        size_t produced = 0u;
        const uint64_t request = target_elapsed - elapsed < 512u ? target_elapsed - elapsed : 512u;
        gbb_run_result br = gbb_run_audio(split, request, b + bc, 512u - bc, &produced);
        ok = br.reason == GBB_STOP_BUDGET && br.consumed_half_dots != 0u;
        elapsed += br.consumed_half_dots;
        bc += produced;
    }
    ok = ok && ac == bc && memcmp(a, b, ac * sizeof(a[0])) == 0;
    ok = ok && gbb_reset(split) == GBB_OK;
    ok = ok && gbb_reset(split) == GBB_OK;
    gbb_destroy(whole);
    gbb_destroy(split);
    return ok ? 0 : 1;
}

static int timeline_halt_stop(void) {
    static const uint8_t halt_program[] = {0x76u};
    static const uint8_t stop_program[] = {0x10u,0x00u};
    gbb_instance *halt = machine_with_program(halt_program, sizeof(halt_program));
    gbb_instance *stop = machine_with_program(stop_program, sizeof(stop_program));
    if (halt == NULL || stop == NULL) { gbb_destroy(halt); gbb_destroy(stop); return 1; }
    gbb_audio_frame frames[16] = {{0}};
    size_t count = 0u;
    gbb_run_result hr = gbb_run_audio(halt, 512u, frames, 16u, &count);
    int ok = hr.reason == GBB_STOP_HALTED_IDLE && hr.consumed_half_dots == 8u;
    count = 0u;
    hr = gbb_run_audio(halt, 512u, frames, 16u, &count);
    ok = ok && hr.reason == GBB_STOP_HALTED_IDLE && hr.consumed_half_dots == 512u && count == 2u;
    count = 0u;
    gbb_run_result sr = gbb_run_audio(stop, 512u, frames, 16u, &count);
    ok = ok && sr.reason == GBB_STOP_STOPPED && count == 0u;
    sr = gbb_run_audio(stop, 8192u, frames, 16u, &count);
    ok = ok && sr.reason == GBB_STOP_STOPPED && sr.consumed_half_dots == 8192u && count == 0u;
    gbb_destroy(halt);
    gbb_destroy(stop);
    return ok ? 0 : 1;
}

static int wave_channel(void) {
    static const uint8_t program[] = {
        0x3E,0x80,0xE0,0x26, 0x3E,0xF0,0xE0,0x30,
        0xF0,0x30,0xEA,0x00,0xC0, 0x3E,0x80,0xE0,0x1A,
        0x3E,0x80,0xE0,0x1A, 0x3E,0x40,0xE0,0x1B,
        0x3E,0x20,0xE0,0x1C, 0x3E,0xFF,0xE0,0x1D,
        0x3E,0xC7,0xE0,0x1E, 0x3E,0x47,0xE0,0x24,
        0x3E,0x44,0xE0,0x25, 0xF0,0x1A,0xEA,0x01,0xC0,
        0xF0,0x1E,0xEA,0x02,0xC0, 0xF0,0x26,0xEA,0x03,0xC0,
        0x18,0xFE
    };
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    gbb_audio_frame frames[32] = {{0}};
    size_t count = 0u;
    gbb_run_result r = gbb_run_audio(m, 4096u, frames, 32u, &count);
    int audible = 0;
    for (size_t i = 0u; i < count; ++i) audible |= frames[i].right != 0;
    int ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC000u) == 0xF0u &&
             gbb_peek_ram(m, 0xC001u) == 0xFFu &&
             gbb_peek_ram(m, 0xC002u) == 0xFFu &&
             gbb_peek_ram(m, 0xC003u) == 0xF4u && audible;
    if (!ok) fprintf(stderr, "wave reason=%d count=%zu state=%02x,%02x,%02x,%02x audible=%d\n",
                     r.reason, count, gbb_peek_ram(m, 0xC000u),
                     gbb_peek_ram(m, 0xC001u), gbb_peek_ram(m, 0xC002u),
                     gbb_peek_ram(m, 0xC003u), audible);
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
    if (strcmp(name, "apu_mixer") == 0) {
        if (mixer_channels() != 0) { printf("not ok 1 - apu_mixer\n"); return 1; }
        printf("ok 1 - apu_mixer\n"); return 0;
    }
    if (strcmp(name, "apu_sequencer") == 0) {
        if (sequencer_div_write() != 0) { printf("not ok 1 - apu_sequencer\n"); return 1; }
        printf("ok 1 - apu_sequencer\n"); return 0;
    }
    if (strcmp(name, "apu_timeline") == 0) {
        if (timeline_partition() != 0 || timeline_halt_stop() != 0) {
            printf("not ok 1 - apu_timeline\n"); return 1;
        }
        printf("ok 1 - apu_timeline\n"); return 0;
    }
    if (strcmp(name, "apu_wave") == 0) {
        if (wave_channel() != 0) { printf("not ok 1 - apu_wave\n"); return 1; }
        printf("ok 1 - apu_wave\n"); return 0;
    }
    printf("not ok 1 - %s # case not implemented yet\n", name);
    return 1;
}
