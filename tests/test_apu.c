#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Authored register programs exercise the deterministic DMG software model, not hardware. */

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

static void emit_write(uint8_t *program, size_t *length, uint8_t reg,
                       uint8_t value);

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

static int wave_active_alias(void) {
    static const uint8_t program[] = {
        0x3Eu,0x80u,0xE0u,0x1Au, 0x3Eu,0x20u,0xE0u,0x1Cu,
        0x3Eu,0x00u,0xE0u,0x1Du, 0x3Eu,0x80u,0xE0u,0x1Eu,
        0x3Eu,0xF0u,0xE0u,0x3Fu, 0xF0u,0x30u,0xEAu,0x00u,0xC0u,
        0x18u,0xFEu
    };
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    const gbb_run_result result = gbb_run(m, 256u, NULL, 0u);
    const uint8_t current_byte = gbb_peek_ram(m, 0xC000u);
    gbb_destroy(m);
    return result.reason == GBB_STOP_BUDGET && current_byte == 0xF0u ? 0 : 1;
}

static int noise_channel(void) {
    static const uint8_t program[] = {
        0x3E,0x80,0xE0,0x26, 0x3E,0x3F,0xE0,0x20,
        0x3E,0xF2,0xE0,0x21, 0x3E,0x08,0xE0,0x22,
        0x3E,0xC0,0xE0,0x23, 0x3E,0x07,0xE0,0x24,
        0x3E,0x08,0xE0,0x25,
        0xF0,0x21,0xEA,0x00,0xC0, 0xF0,0x22,0xEA,0x01,0xC0,
        0xF0,0x23,0xEA,0x02,0xC0, 0xF0,0x26,0xEA,0x03,0xC0,
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
             gbb_peek_ram(m, 0xC000u) == 0xF2u &&
             gbb_peek_ram(m, 0xC001u) == 0x08u &&
             gbb_peek_ram(m, 0xC002u) == 0xFFu &&
             gbb_peek_ram(m, 0xC003u) == 0xF8u && audible;
    if (!ok) fprintf(stderr, "noise reason=%d count=%zu state=%02x,%02x,%02x,%02x audible=%d\n",
                     r.reason, count, gbb_peek_ram(m, 0xC000u),
                     gbb_peek_ram(m, 0xC001u), gbb_peek_ram(m, 0xC002u),
                     gbb_peek_ram(m, 0xC003u), audible);
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int run_pulse_envelope(uint8_t envelope, gbb_audio_frame *frames,
                              size_t capacity, size_t *count) {
    uint8_t program[64];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x11u, 0x80u);
    emit_write(program, &length, 0x12u, envelope);
    emit_write(program, &length, 0x13u, 0xF8u);
    emit_write(program, &length, 0x14u, 0x87u);
    emit_write(program, &length, 0x24u, 0x00u);
    emit_write(program, &length, 0x25u, 0x11u);
    program[length++] = 0x18u;
    program[length++] = 0xFEu;
    gbb_instance *m = machine_with_delayed_program(program, length, 0u);
    if (m == NULL) return 1;
    const gbb_run_result result = gbb_run_audio(m, 300000u, frames, capacity, count);
    const int ok = result.reason == GBB_STOP_BUDGET &&
        result.consumed_half_dots <= 300000u &&
        300000u - result.consumed_half_dots <= 40u && *count > 1500u;
    if (!ok) fprintf(stderr, "envelope run reason=%d elapsed=%llu count=%zu\n",
                     result.reason, (unsigned long long)result.consumed_half_dots,
                     *count);
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int pulse_envelope_transition(void) {
    gbb_audio_frame ramped[1800] = {{0}}, steady[1800] = {{0}};
    size_t ramped_count = 0u, steady_count = 0u;
    if (run_pulse_envelope(0x99u, ramped, 1800u, &ramped_count) != 0 ||
        run_pulse_envelope(0x90u, steady, 1800u, &steady_count) != 0 ||
        ramped_count != steady_count || ramped_count <= 1000u)
        return 1;
    if (memcmp(ramped, steady, 300u * sizeof(*ramped)) != 0) return 1;
    int ramped_peak = 0, steady_peak = 0;
    for (size_t i = 800u; i < ramped_count; ++i) {
        if (ramped[i].left > ramped_peak) ramped_peak = ramped[i].left;
        if (steady[i].left > steady_peak) steady_peak = steady[i].left;
    }
    if (ramped_peak <= steady_peak) {
        fprintf(stderr, "envelope peaks ramped=%d steady=%d\n",
                ramped_peak, steady_peak);
        return 1;
    }
    return 0;
}

static void emit_write(uint8_t *program, size_t *length, uint8_t reg, uint8_t value) {
    program[(*length)++] = 0x3Eu;
    program[(*length)++] = value;
    program[(*length)++] = 0xE0u;
    program[(*length)++] = reg;
}

static int run_wave_pattern(uint8_t repeated_byte, gbb_audio_frame *frames,
                            size_t capacity, size_t *count) {
    uint8_t program[192];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    for (uint8_t reg = 0x30u; reg <= 0x3Fu; ++reg)
        emit_write(program, &length, reg, repeated_byte);
    emit_write(program, &length, 0x1Au, 0x80u);
    emit_write(program, &length, 0x1Cu, 0x20u);
    emit_write(program, &length, 0x1Du, 0xF8u);
    emit_write(program, &length, 0x1Eu, 0x87u);
    emit_write(program, &length, 0x24u, 0x77u);
    emit_write(program, &length, 0x25u, 0x44u);
    program[length++] = 0x18u;
    program[length++] = 0xFEu;
    gbb_instance *m = machine_with_delayed_program(program, length, 0u);
    if (m == NULL) return 1;
    const gbb_run_result result = gbb_run_audio(m, 32768u, frames, capacity, count);
    const int ok = result.reason == GBB_STOP_BUDGET &&
        result.consumed_half_dots <= 32768u &&
        32768u - result.consumed_half_dots <= 40u && *count > 100u;
    if (!ok) fprintf(stderr, "wave run reason=%d elapsed=%llu count=%zu\n",
                     result.reason, (unsigned long long)result.consumed_half_dots,
                     *count);
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int wave_nibble_pattern(void) {
    gbb_audio_frame high_low[256] = {{0}}, both_high[256] = {{0}};
    gbb_audio_frame low_high[256] = {{0}}, both_low[256] = {{0}};
    size_t high_low_count = 0u, both_high_count = 0u;
    size_t low_high_count = 0u, both_low_count = 0u;
    if (run_wave_pattern(0xF0u, high_low, 256u, &high_low_count) != 0 ||
        run_wave_pattern(0xFFu, both_high, 256u, &both_high_count) != 0 ||
        run_wave_pattern(0x0Fu, low_high, 256u, &low_high_count) != 0 ||
        run_wave_pattern(0x00u, both_low, 256u, &both_low_count) != 0)
        return 1;
    if (high_low_count != both_high_count || low_high_count != both_low_count ||
        memcmp(high_low, both_high, high_low_count * sizeof(*high_low)) == 0 ||
        memcmp(low_high, both_low, low_high_count * sizeof(*low_high)) == 0 ||
        memcmp(low_high, both_high, low_high_count * sizeof(*low_high)) == 0) {
        fprintf(stderr, "wave pattern counts=%zu,%zu,%zu,%zu low-equal=%d high-equal=%d\n",
                high_low_count, both_high_count, low_high_count, both_low_count,
                memcmp(high_low, both_high, high_low_count * sizeof(*high_low)) == 0,
                memcmp(low_high, both_low, low_high_count * sizeof(*low_high)) == 0);
        return 1;
    }
    return 0;
}

static int run_noise_width(uint8_t polynomial, gbb_audio_frame *frames,
                           size_t capacity, size_t *count) {
    static const uint8_t setup[][2] = {
        {0x26u,0x80u}, {0x21u,0xF0u}, {0x24u,0x77u}, {0x25u,0x88u}
    };
    uint8_t program[64];
    size_t length = 0u;
    for (size_t i = 0u; i < sizeof(setup) / sizeof(setup[0]); ++i)
        emit_write(program, &length, setup[i][0], setup[i][1]);
    emit_write(program, &length, 0x22u, polynomial);
    emit_write(program, &length, 0x23u, 0x80u);
    program[length++] = 0x18u;
    program[length++] = 0xFEu;
    gbb_instance *m = machine_with_delayed_program(program, length, 0u);
    if (m == NULL) return 1;
    const gbb_run_result result = gbb_run_audio(m, 32768u, frames, capacity, count);
    const int ok = result.reason == GBB_STOP_BUDGET &&
        result.consumed_half_dots <= 32768u &&
        32768u - result.consumed_half_dots <= 40u && *count > 100u;
    gbb_destroy(m);
    return ok ? 0 : 1;
}

static int noise_width_pattern(void) {
    gbb_audio_frame wide[256] = {{0}}, narrow[256] = {{0}};
    gbb_audio_frame repeated[256] = {{0}};
    size_t wide_count = 0u, narrow_count = 0u, repeated_count = 0u;
    if (run_noise_width(0x00u, wide, 256u, &wide_count) != 0 ||
        run_noise_width(0x08u, narrow, 256u, &narrow_count) != 0 ||
        run_noise_width(0x08u, repeated, 256u, &repeated_count) != 0)
        return 1;
    if (wide_count != narrow_count || narrow_count != repeated_count ||
        memcmp(wide, narrow, wide_count * sizeof(*wide)) == 0 ||
        memcmp(narrow, repeated, narrow_count * sizeof(*narrow)) != 0)
        return 1;
    return 0;
}

static int pulse_sweep_overflow(void) {
    static const uint8_t program[] = {
        0x3Eu,0x80u,0xE0u,0x26u, 0x3Eu,0x01u,0xE0u,0x10u,
        0x3Eu,0x80u,0xE0u,0x11u, 0x3Eu,0xF0u,0xE0u,0x12u,
        0x3Eu,0xFFu,0xE0u,0x13u, 0x3Eu,0x87u,0xE0u,0x14u,
        0xF0u,0x26u,0xEAu,0x00u,0xC0u, 0x18u,0xFEu
    };
    gbb_instance *m = machine_with_program(program, sizeof(program));
    if (m == NULL) return 1;
    const gbb_run_result result = gbb_run(m, 512u, NULL, 0u);
    const uint8_t status = gbb_peek_ram(m, 0xC000u);
    gbb_destroy(m);
    return result.reason == GBB_STOP_BUDGET && (status & 0x01u) == 0u ? 0 : 1;
}

static int channel_power_matrix(void) {
    static const uint8_t setup[][2] = {
        {0x26,0x80}, {0x11,0x80}, {0x12,0xF0}, {0x14,0x80},
        {0x16,0x80}, {0x17,0xF0}, {0x19,0x80},
        {0x30,0xFF}, {0x1A,0x80}, {0x1C,0x20}, {0x1E,0x80},
        {0x20,0x3F}, {0x21,0xF0}, {0x22,0x00}, {0x23,0x80}
    };
    for (unsigned mask = 0u; mask < 16u; ++mask) {
        uint8_t program[192];
        size_t n = 0u;
        program[n++] = 0xF0u; program[n++] = 0x26u;
        program[n++] = 0xEAu; program[n++] = 0x01u;
        program[n++] = 0xC0u;
        for (size_t i = 0u; i < sizeof(setup) / sizeof(setup[0]); ++i)
            emit_write(program, &n, setup[i][0], setup[i][1]);
        if ((mask & 1u) == 0u) emit_write(program, &n, 0x12u, 0x00u);
        if ((mask & 2u) == 0u) emit_write(program, &n, 0x17u, 0x00u);
        if ((mask & 4u) == 0u) emit_write(program, &n, 0x1Au, 0x00u);
        if ((mask & 8u) == 0u) emit_write(program, &n, 0x21u, 0x00u);
        program[n++] = 0xF0u; program[n++] = 0x26u;
        program[n++] = 0xEAu; program[n++] = 0x00u;
        program[n++] = 0xC0u; program[n++] = 0x18u; program[n++] = 0xFEu;
        gbb_instance *m = machine_with_delayed_program(program, n, 0u);
        if (m == NULL) return 1;
        gbb_run_result r = gbb_run(m, 8192u, NULL, 0u);
        int ok = r.reason == GBB_STOP_BUDGET &&
                 gbb_peek_ram(m, 0xC001u) == 0xF0u &&
                 gbb_peek_ram(m, 0xC000u) == (uint8_t)(0xF0u | mask);
        if (!ok) fprintf(stderr, "power mask=%u reason=%d initial=%02x status=%02x expected=%02x\n",
                         mask, r.reason, gbb_peek_ram(m, 0xC001u),
                         gbb_peek_ram(m, 0xC000u), (unsigned)(0xF0u | mask));
        gbb_destroy(m);
        if (!ok) return 1;
    }
    return 0;
}

static int power_transitions(void) {
    static const uint8_t program[] = {
        0xF0,0x26,0xEA,0x05,0xC0, 0xF0,0x30,0xEA,0x06,0xC0,
        0x3E,0x80,0xE0,0x26,
        0x3E,0x80,0xE0,0x11, 0x3E,0xF0,0xE0,0x12, 0x3E,0x80,0xE0,0x14,
        0x3E,0x80,0xE0,0x16, 0x3E,0xF0,0xE0,0x17, 0x3E,0x80,0xE0,0x19,
        0x3E,0xF0,0xE0,0x30, 0x3E,0x80,0xE0,0x1A,
        0x3E,0x20,0xE0,0x1C, 0x3E,0x80,0xE0,0x1E,
        0x3E,0x3F,0xE0,0x20, 0x3E,0xF0,0xE0,0x21, 0x3E,0x80,0xE0,0x23,
        0xF0,0x26,0xEA,0x00,0xC0, 0xAF,0xE0,0x26,
        0xF0,0x26,0xEA,0x01,0xC0, 0x3E,0xFF,0xE0,0x21,
        0x3E,0x80,0xE0,0x26, 0xF0,0x26,0xEA,0x02,0xC0,
        0xF0,0x21,0xEA,0x03,0xC0, 0xF0,0x30,0xEA,0x04,0xC0,
        0x18,0xFE
    };
    gbb_instance *m = machine_with_delayed_program(program, sizeof(program), 0u);
    if (m == NULL) return 1;
    gbb_run_result r = gbb_run(m, 8192u, NULL, 0u);
    int ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC000u) == 0xFFu &&
             gbb_peek_ram(m, 0xC001u) == 0x70u &&
             gbb_peek_ram(m, 0xC002u) == 0xF0u &&
             gbb_peek_ram(m, 0xC003u) == 0x00u &&
             gbb_peek_ram(m, 0xC004u) == 0xF0u;
    if (!ok) fprintf(stderr, "transitions reason=%d statuses=%02x,%02x,%02x\n",
                     r.reason, gbb_peek_ram(m, 0xC000u),
                     gbb_peek_ram(m, 0xC001u), gbb_peek_ram(m, 0xC002u));
    ok = ok && gbb_reset(m) == GBB_OK;
    if (ok) {
        r = gbb_run(m, 144u, NULL, 0u);
        ok = r.reason == GBB_STOP_BUDGET &&
             gbb_peek_ram(m, 0xC005u) == 0xF0u &&
             gbb_peek_ram(m, 0xC006u) == 0x00u;
    }
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
        if (wave_channel() != 0 || wave_active_alias() != 0 ||
            wave_nibble_pattern() != 0) {
            printf("not ok 1 - apu_wave\n"); return 1;
        }
        printf("ok 1 - apu_wave\n"); return 0;
    }
    if (strcmp(name, "apu_noise") == 0) {
        if (noise_channel() != 0 || noise_width_pattern() != 0) {
            printf("not ok 1 - apu_noise\n"); return 1;
        }
        printf("ok 1 - apu_noise\n"); return 0;
    }
    if (strcmp(name, "apu_envelope") == 0) {
        if (pulse_envelope_transition() != 0) {
            printf("not ok 1 - apu_envelope\n"); return 1;
        }
        printf("ok 1 - apu_envelope\n"); return 0;
    }
    if (strcmp(name, "apu_sweep") == 0) {
        if (pulse_sweep_overflow() != 0) {
            printf("not ok 1 - apu_sweep\n"); return 1;
        }
        printf("ok 1 - apu_sweep\n"); return 0;
    }
    if (strcmp(name, "apu_power") == 0) {
        if (channel_power_matrix() != 0 || power_transitions() != 0) {
            printf("not ok 1 - apu_power\n"); return 1;
        }
        printf("ok 1 - apu_power\n"); return 0;
    }
    printf("not ok 1 - %s # case not implemented yet\n", name);
    return 1;
}
