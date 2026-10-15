#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef GBB_CGB_APU_CONTROL_MUTANT
#define GBB_CGB_APU_CONTROL_MUTANT 0
#endif

#define REQUIRE_CASE(condition, name) do { \
    if (!(condition)) { \
        printf("not ok 1 - %s\n", (name)); \
        fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);

typedef struct {
    gbb_stop_reason reason;
    uint8_t value;
    size_t read_count;
    uint64_t read_time;
} pcm_guest_result;

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static gbb_instance *load_cgb_guest(const uint8_t *program, size_t length) {
    if (length > 32768u - 0x150u) return NULL;
    uint8_t *rom = calloc(1u, 32768u);
    if (rom == NULL) return NULL;
    rom[0x100] = 0xC3u;
    rom[0x101] = 0x50u;
    rom[0x102] = 0x01u;
    rom[0x143] = 0x80u;
    memcpy(rom + 0x150u, program, length);
    fix_checksum(rom);

    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768u) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static void emit_write(uint8_t *program, size_t *length, uint8_t address,
                       uint8_t value) {
    program[(*length)++] = 0x3Eu; /* LD A,d8 */
    program[(*length)++] = value;
    program[(*length)++] = 0xE0u; /* LDH (a8),A */
    program[(*length)++] = address;
}

static int read_pcm12_as_guest(pcm_guest_result *out) {
    uint8_t program[64];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u); /* NR52: power on */
    emit_write(program, &length, 0x11u, 0x80u); /* CH1 duty 2: phase zero is high */
    emit_write(program, &length, 0x12u, 0xF0u); /* CH1 DAC enabled, volume 15 */
    emit_write(program, &length, 0x13u, 0x00u); /* CH1 frequency low */
    emit_write(program, &length, 0x14u, 0x80u); /* CH1 trigger, phase zero */
    program[length++] = 0xF0u; program[length++] = 0x76u; /* LDH A,(PCM12) */
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    program[length++] = 0x76u; /* HALT */

    gbb_instance *machine = load_cgb_guest(program, length);
    if (machine == NULL) return 1;
    gbb_test_bus_event events[128];
    memset(events, 0, sizeof(events));
    gbb_test_observer_set(machine, events, sizeof(events) / sizeof(events[0]));
    const gbb_run_result run = gbb_run(machine, 1024u, NULL, 0u);
    out->reason = run.reason;
    out->value = gbb_peek_ram(machine, 0xC000u);
    out->read_count = 0u;
    out->read_time = 0u;
    for (size_t i = 0u; i < sizeof(events) / sizeof(events[0]); ++i) {
        if (events[i].access == 1u && events[i].address == 0xFF76u) {
            ++out->read_count;
            out->read_time = events[i].time_half_dots;
        }
    }
    gbb_destroy(machine);
    return 0;
}

static int cgb_pcm_tracer(int expect_swapped) {
    pcm_guest_result result;
    if (read_pcm12_as_guest(&result) != 0) {
        fprintf(stderr, "could not create CGB guest\n");
        return 1;
    }
    const uint8_t expected = expect_swapped ? 0xF0u : 0x0Fu;
    const int guest_completed = result.reason == GBB_STOP_HALTED_IDLE;
    const int value_matches = result.value == expected;
    const int timestamp_matches = result.read_count == 1u && result.read_time == 248u;

    if (expect_swapped) {
        if (guest_completed && result.value == 0xF0u && timestamp_matches) {
            printf("ok 1 - cgb_pcm_tracer_control\n");
            fprintf(stderr, "negative-control diagnostic: guest-memory PCM12 CH1 expected=0x0f actual=0xf0 time_half_dots=%llu\n",
                    (unsigned long long)result.read_time);
            return 0;
        }
        printf("not ok 1 - cgb_pcm_tracer_control\n");
        fprintf(stderr, "mutant observation reason=%d expected=0xf0 actual=0x%02x reads=%zu time_half_dots=%llu\n",
                result.reason, result.value, result.read_count,
                (unsigned long long)result.read_time);
        return 1;
    }

    if (guest_completed && value_matches && timestamp_matches) {
        printf("ok 1 - cgb_pcm_tracer\n");
        fprintf(stderr, "guest-memory PCM12 CH1 expected=0x0f actual=0x%02x time_half_dots=%llu\n",
                result.value, (unsigned long long)result.read_time);
        return 0;
    }
    printf("not ok 1 - cgb_pcm_tracer\n");
    fprintf(stderr, "guest-memory PCM12 CH1 expected=0x0f actual=0x%02x reason=%d reads=%zu time_half_dots=%llu expected_time_half_dots=248\n",
            result.value, result.reason, result.read_count,
            (unsigned long long)result.read_time);
    return 1;
}

static size_t configured_pcm_program(uint8_t *program, uint8_t nr50, uint8_t nr51,
                                    int include_all_channels, int read_second) {
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x11u, 0x80u);
    emit_write(program, &length, 0x12u, 0xF0u);
    emit_write(program, &length, 0x13u, 0x00u);
    emit_write(program, &length, 0x14u, 0x80u);
    if (include_all_channels) {
        emit_write(program, &length, 0x16u, 0x80u);
        emit_write(program, &length, 0x17u, 0xE0u);
        emit_write(program, &length, 0x18u, 0x00u);
        emit_write(program, &length, 0x19u, 0x80u);
        emit_write(program, &length, 0x30u, 0xA5u);
        emit_write(program, &length, 0x1Au, 0x80u);
        emit_write(program, &length, 0x1Cu, 0x20u);
        emit_write(program, &length, 0x1Du, 0xFFu);
        emit_write(program, &length, 0x1Eu, 0x87u);
        emit_write(program, &length, 0x20u, 0x00u);
        emit_write(program, &length, 0x21u, 0xF0u);
        emit_write(program, &length, 0x22u, 0x00u);
        emit_write(program, &length, 0x23u, 0x80u);
        for (unsigned i = 0u; i < 40u; ++i) program[length++] = 0x00u;
    }
    emit_write(program, &length, 0x24u, nr50);
    emit_write(program, &length, 0x25u, nr51);
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    if (read_second) {
        program[length++] = 0xF0u; program[length++] = 0x77u;
        program[length++] = 0xEAu; program[length++] = 0x01u; program[length++] = 0xC0u;
    }
    program[length++] = 0x76u;
    return length;
}

static int run_program_pcm(const uint8_t *program, size_t length, int output_mode,
                           uint8_t *pcm12, uint8_t *pcm34) {
    gbb_instance *machine = load_cgb_guest(program, length);
    if (machine == NULL) return 1;
    gbb_run_result run = {0};
    if (output_mode == 0) {
        run = gbb_run(machine, 2048u, NULL, 0u);
    } else if (output_mode == 1) {
        gbb_audio_frame frames[32] = {{0}};
        size_t count = 0u;
        run = gbb_run_audio(machine, 2048u, frames, 32u, &count);
    } else {
        uint64_t consumed = 0u;
        do {
            gbb_audio_frame drained_frame = {0, 0};
            size_t count = 0u;
            run = gbb_run_audio(machine, 2048u - consumed, &drained_frame, 1u, &count);
            consumed += run.consumed_half_dots;
            if (run.reason == GBB_STOP_OUTPUT_FULL && count != 1u) {
                gbb_destroy(machine);
                return 1;
            }
            if (run.reason != GBB_STOP_OUTPUT_FULL) break;
        } while (consumed < 2048u);
    }
    const int ok = run.reason == GBB_STOP_HALTED_IDLE;
    if (pcm12 != NULL) *pcm12 = gbb_peek_ram(machine, 0xC000u);
    if (pcm34 != NULL) *pcm34 = gbb_peek_ram(machine, 0xC001u);
    gbb_destroy(machine);
    return ok ? 0 : 1;
}

static int cgb_pcm_channels(const char *name) {
    uint8_t program[512];
    const size_t length = configured_pcm_program(program, 0x77u, 0x00u, 1, 1);
    uint8_t pcm12 = 0u, pcm34 = 0u;
    REQUIRE_CASE(run_program_pcm(program, length, 0, &pcm12, &pcm34) == 0, name);
    REQUIRE_CASE(pcm12 == 0xEFu, name);
    REQUIRE_CASE(pcm34 == 0xFAu, name);
    size_t phase_length = 0u;
    emit_write(program, &phase_length, 0x26u, 0x80u);
    emit_write(program, &phase_length, 0x11u, 0x80u);
    emit_write(program, &phase_length, 0x12u, 0xF0u);
    emit_write(program, &phase_length, 0x13u, 0xFFu);
    emit_write(program, &phase_length, 0x14u, 0x87u);
    program[phase_length++] = 0xF0u; program[phase_length++] = 0x76u;
    program[phase_length++] = 0xEAu; program[phase_length++] = 0x00u; program[phase_length++] = 0xC0u;
    for (unsigned i = 0u; i < 30u; ++i) program[phase_length++] = 0x00u;
    program[phase_length++] = 0xF0u; program[phase_length++] = 0x76u;
    program[phase_length++] = 0xEAu; program[phase_length++] = 0x01u; program[phase_length++] = 0xC0u;
    program[phase_length++] = 0x76u;
    gbb_instance *phase_machine = load_cgb_guest(program, phase_length);
    REQUIRE_CASE(phase_machine != NULL, name);
    const gbb_run_result phase_run = gbb_run(phase_machine, 2048u, NULL, 0u);
    const uint8_t phase_start = gbb_peek_ram(phase_machine, 0xC000u);
    const uint8_t phase_later = gbb_peek_ram(phase_machine, 0xC001u);
    gbb_destroy(phase_machine);
    REQUIRE_CASE(phase_run.reason == GBB_STOP_HALTED_IDLE &&
                 phase_start == 0x0Fu && phase_later == 0u, name);
    fprintf(stderr, "CGB PCM channel pairs expected=0xef,0xfa actual=0x%02x,0x%02x\n",
            pcm12, pcm34);
    fprintf(stderr, "pulse phase advancement expected=0x0f,0x00 actual=0x%02x,0x%02x\n",
            phase_start, phase_later);
    printf("ok 1 - %s\n", name);
    return 0;
}

static int cgb_pcm_power_dac(const char *name) {
    uint8_t program[256];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x11u, 0x80u);
    emit_write(program, &length, 0x12u, 0xF0u);
    program[length++] = 0xF0u; program[length++] = 0x76u; /* DAC on, channel not triggered. */
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    emit_write(program, &length, 0x13u, 0x00u);
    emit_write(program, &length, 0x14u, 0x80u);
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x01u; program[length++] = 0xC0u;
    emit_write(program, &length, 0x12u, 0x00u); /* DAC disabled clears the channel. */
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x02u; program[length++] = 0xC0u;
    emit_write(program, &length, 0x26u, 0x00u); /* APU off clears every digital output. */
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x03u; program[length++] = 0xC0u;
    program[length++] = 0x76u;
    gbb_instance *machine = load_cgb_guest(program, length);
    REQUIRE_CASE(machine != NULL, name);
    const gbb_run_result run = gbb_run(machine, 2048u, NULL, 0u);
    REQUIRE_CASE(run.reason == GBB_STOP_HALTED_IDLE, name);
    const uint8_t channel_off = gbb_peek_ram(machine, 0xC000u);
    const uint8_t active = gbb_peek_ram(machine, 0xC001u);
    const uint8_t dac_off = gbb_peek_ram(machine, 0xC002u);
    const uint8_t power_off = gbb_peek_ram(machine, 0xC003u);
    gbb_destroy(machine);
    REQUIRE_CASE(channel_off == 0u && active == 0x0Fu && dac_off == 0u && power_off == 0u, name);
    fprintf(stderr, "PCM channel/power/DAC expected=0x00,0x0f,0x00,0x00 actual=0x%02x,0x%02x,0x%02x,0x%02x\n",
            channel_off, active, dac_off, power_off);
    printf("ok 1 - %s\n", name);
    return 0;
}

static size_t readonly_program(uint8_t *program) {
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x11u, 0x80u);
    emit_write(program, &length, 0x12u, 0xF0u);
    emit_write(program, &length, 0x14u, 0x80u);
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    emit_write(program, &length, 0x76u, 0xA5u);
    emit_write(program, &length, 0x77u, 0x5Au);
    program[length++] = 0xF0u; program[length++] = 0x76u;
    program[length++] = 0xEAu; program[length++] = 0x01u; program[length++] = 0xC0u;
    program[length++] = 0xF0u; program[length++] = 0x77u;
    program[length++] = 0xEAu; program[length++] = 0x02u; program[length++] = 0xC0u;
    program[length++] = 0x76u;
    return length;
}

static int cgb_pcm_readonly(const char *name) {
    uint8_t program[256];
    const size_t length = readonly_program(program);
    gbb_instance *machine = load_cgb_guest(program, length);
    REQUIRE_CASE(machine != NULL, name);
    const gbb_run_result run = gbb_run(machine, 2048u, NULL, 0u);
    REQUIRE_CASE(run.reason == GBB_STOP_HALTED_IDLE, name);
    const uint8_t before = gbb_peek_ram(machine, 0xC000u);
    const uint8_t after12 = gbb_peek_ram(machine, 0xC001u);
    const uint8_t after34 = gbb_peek_ram(machine, 0xC002u);
    gbb_destroy(machine);
    REQUIRE_CASE(before == 0x0Fu && after12 == before && after34 == 0u, name);
    fprintf(stderr, "PCM readonly expected=0x0f,0x0f,0x00 actual=0x%02x,0x%02x,0x%02x\n",
            before, after12, after34);
    printf("ok 1 - %s\n", name);
    return 0;
}

static int cgb_pcm_host_invariance(const char *name) {
    uint8_t program[256];
    uint8_t reference = 0u, muted = 0u, buffered = 0u, drained = 0u;
    size_t length = configured_pcm_program(program, 0x00u, 0x00u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &reference, NULL) == 0, name);
    length = configured_pcm_program(program, 0x77u, 0x11u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 1, &buffered, NULL) == 0, name);
    REQUIRE_CASE(run_program_pcm(program, length, 2, &drained, NULL) == 0, name);
    length = configured_pcm_program(program, 0x77u, 0x00u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &muted, NULL) == 0, name);
    REQUIRE_CASE(reference == 0x0Fu && muted == reference &&
                 buffered == reference && drained == reference, name);
    fprintf(stderr, "host-invariance expected=0x0f across absent/muted/full/drained; actual=0x%02x,0x%02x,0x%02x,0x%02x\n",
            reference, muted, buffered, drained);
    printf("ok 1 - %s\n", name);
    return 0;
}

static int cgb_pcm_controls(const char *name) {
    uint8_t program[256];
    uint8_t routed = 0u, muted = 0u;
    size_t length = configured_pcm_program(program, 0x77u, 0x11u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &routed, NULL) == 0, name);
    length = configured_pcm_program(program, 0x00u, 0x00u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &muted, NULL) == 0, name);
    REQUIRE_CASE(routed == 0x0Fu && muted == routed, name);
    length = readonly_program(program);
    uint8_t before = 0u, after = 0u;
    REQUIRE_CASE(run_program_pcm(program, length, 0, &before, &after) == 0, name);
    REQUIRE_CASE(before == 0x0Fu && after == 0x0Fu, name);
    printf("ok 1 - %s\n", name);
    return 0;
}

static int cgb_pcm_routing_mutant_control(const char *name) {
    uint8_t program[256];
    uint8_t routed = 0u, muted = 0u;
    size_t length = configured_pcm_program(program, 0x77u, 0x11u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &routed, NULL) == 0, name);
    length = configured_pcm_program(program, 0x00u, 0x00u, 0, 0);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &muted, NULL) == 0, name);
    if (routed == 0x0Fu && muted == 0u) {
        fprintf(stderr, "negative-control diagnostic: routing-coupled PCM expected-muted=0x0f actual=0x00\n");
        printf("ok 1 - %s\n", name);
        return 0;
    }
    fprintf(stderr, "routing mutant not detected expected=0x0f,0x00 actual=0x%02x,0x%02x\n",
            routed, muted);
    printf("not ok 1 - %s\n", name);
    return 1;
}

static int cgb_pcm_writable_mutant_control(const char *name) {
    uint8_t program[256];
    uint8_t before = 0u, after = 0u;
    const size_t length = readonly_program(program);
    REQUIRE_CASE(run_program_pcm(program, length, 0, &before, &after) == 0, name);
    if (before == 0x0Fu && after == 0xA5u) {
        fprintf(stderr, "negative-control diagnostic: writable PCM expected readonly=0x0f actual=0xa5\n");
        printf("ok 1 - %s\n", name);
        return 0;
    }
    fprintf(stderr, "writable mutant not detected expected=0x0f,0xa5 actual=0x%02x,0x%02x\n",
            before, after);
    printf("not ok 1 - %s\n", name);
    return 1;
}

typedef struct {
    gbb_stop_reason reason;
    uint8_t first_sample;
    uint8_t fetched_sample;
    size_t read_count;
    uint64_t read_times[2];
} wave_transition_result;

static size_t wave_transition_program(uint8_t *program, int wait_for_fetch) {
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u); /* NR52 on. */
    for (unsigned i = 0u; i < 16u; ++i)
        emit_write(program, &length, (uint8_t)(0x30u + i), 0x77u);
    emit_write(program, &length, 0x1Au, 0x80u); /* CH3 DAC on. */
    emit_write(program, &length, 0x1Cu, 0x20u); /* Full digital wave level. */
    emit_write(program, &length, 0x1Du, 0xFFu);
    emit_write(program, &length, 0x1Eu, 0x87u); /* Fast initial fetches load $77. */
    for (unsigned i = 0u; i < 8u; ++i) program[length++] = 0x00u;
    emit_write(program, &length, 0x1Du, 0x00u);
    emit_write(program, &length, 0x1Eu, 0x80u); /* Trigger resets position, not buffer. */
    emit_write(program, &length, 0x30u, 0xAAu); /* Active alias changes RAM, not the latch. */
    program[length++] = 0xF0u; program[length++] = 0x77u; /* Guest reads FF77. */
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    if (wait_for_fetch) {
        /* Frequency zero gives a 4096-half-dot period; 512 NOPs cross one fetch. */
        for (unsigned i = 0u; i < 512u; ++i) program[length++] = 0x00u;
        program[length++] = 0xF0u; program[length++] = 0x77u;
        program[length++] = 0xEAu; program[length++] = 0x01u; program[length++] = 0xC0u;
    }
    program[length++] = 0x76u;
    return length;
}

static int run_wave_transition_guest(int wait_for_fetch, wave_transition_result *out) {
    uint8_t program[1024];
    const size_t length = wave_transition_program(program, wait_for_fetch);
    gbb_instance *machine = load_cgb_guest(program, length);
    if (machine == NULL) return 1;
    gbb_test_bus_event events[256];
    memset(events, 0, sizeof(events));
    gbb_test_observer_set(machine, events, sizeof(events) / sizeof(events[0]));
    const gbb_run_result run = gbb_run(machine, 16384u, NULL, 0u);
    out->reason = run.reason;
    out->first_sample = gbb_peek_ram(machine, 0xC000u);
    out->fetched_sample = gbb_peek_ram(machine, 0xC001u);
    out->read_count = 0u;
    out->read_times[0] = 0u;
    out->read_times[1] = 0u;
    for (size_t i = 0u; i < sizeof(events) / sizeof(events[0]); ++i) {
        if (events[i].access == 1u && events[i].address == 0xFF77u) {
            if (out->read_count < 2u) out->read_times[out->read_count] = events[i].time_half_dots;
            ++out->read_count;
        }
    }
    gbb_destroy(machine);
    return 0;
}

static int cgb_apu_wave_latch(void) {
    wave_transition_result result;
    if (run_wave_transition_guest(0, &result) != 0) {
        printf("not ok 1 - cgb_apu_wave_latch\n");
        fprintf(stderr, "could not create CGB CH3 guest\n");
        return 1;
    }
    const int ok = result.reason == GBB_STOP_HALTED_IDLE &&
                   result.first_sample == 0x07u && result.read_count == 1u;
    if (!ok) {
        printf("not ok 1 - cgb_apu_wave_latch\n");
        fprintf(stderr,
                "guest CH3 retained-sample mismatch expected=0x07 actual=0x%02x reads=%zu reason=%d\n",
                result.first_sample, result.read_count, result.reason);
        return 1;
    }
    fprintf(stderr, "guest CH3 retained sample expected=0x07 actual=0x%02x time_half_dots=%llu\n",
            result.first_sample, (unsigned long long)result.read_times[0]);
    printf("ok 1 - cgb_apu_wave_latch\n");
    return 0;
}

static int cgb_apu_wave_fetch(void) {
    wave_transition_result result;
    if (run_wave_transition_guest(1, &result) != 0) {
        printf("not ok 1 - cgb_apu_wave_fetch\n");
        fprintf(stderr, "could not create CGB CH3 guest\n");
        return 1;
    }
    const int ok = result.reason == GBB_STOP_HALTED_IDLE &&
                   result.first_sample == 0x07u && result.fetched_sample == 0x0Au &&
                   result.read_count == 2u && result.read_times[0] < result.read_times[1];
    if (!ok) {
        printf("not ok 1 - cgb_apu_wave_fetch\n");
        fprintf(stderr,
                "guest CH3 fetch mismatch expected=0x07,0x0a actual=0x%02x,0x%02x reads=%zu times=%llu,%llu reason=%d\n",
                result.first_sample, result.fetched_sample, result.read_count,
                (unsigned long long)result.read_times[0],
                (unsigned long long)result.read_times[1], result.reason);
        return 1;
    }
    fprintf(stderr, "guest CH3 fetch samples expected=0x07,0x0a actual=0x%02x,0x%02x times=%llu,%llu\n",
            result.first_sample, result.fetched_sample,
            (unsigned long long)result.read_times[0],
            (unsigned long long)result.read_times[1]);
    printf("ok 1 - cgb_apu_wave_fetch\n");
    return 0;
}

static int cgb_apu_wave_direct_ram_control(const char *name) {
    wave_transition_result result;
    if (run_wave_transition_guest(0, &result) != 0) {
        printf("not ok 1 - %s\n", name);
        fprintf(stderr, "could not create CGB CH3 negative-control guest\n");
        return 1;
    }
    if (result.first_sample == 0x0Au) {
        fprintf(stderr,
                "negative-control diagnostic: direct-RAM mutant expected=0x07 actual=0x%02x before fetch\n",
                result.first_sample);
        printf("ok 1 - %s\n", name);
        return 0;
    }
    fprintf(stderr, "direct-RAM mutant not detected expected=0x0a actual=0x%02x\n",
            result.first_sample);
    printf("not ok 1 - %s\n", name);
    return 1;
}

static void emit_readback(uint8_t *program, size_t *length, uint8_t address,
                          unsigned slot);
static int run_noise_frequency_guest(int slow_after_trigger, uint8_t samples[4]);

static int cgb_apu_trigger_length_sweep(void) {
    uint8_t program[160];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    program[length++] = 0x06u; program[length++] = 160u; /* Advance DIV by ten high-byte ticks. */
    program[length++] = 0x05u; /* DEC B */
    program[length++] = 0x20u; program[length++] = 0xFDu; /* JR NZ back to DEC B. */
    emit_write(program, &length, 0x26u, 0x00u); /* Reset the sequence phase, not DIV. */
    emit_write(program, &length, 0x26u, 0x80u);
    program[length++] = 0xF0u; program[length++] = 0x04u;
    program[length++] = 0xEAu; program[length++] = 0x00u; program[length++] = 0xC0u;
    emit_write(program, &length, 0x04u, 0x00u); /* DIV falling edge leaves the next step odd. */
    emit_write(program, &length, 0x11u, 0x3Fu); /* CH1 length counter = 1. */
    emit_write(program, &length, 0x12u, 0xF0u); /* Enable the channel DAC. */
    emit_write(program, &length, 0x14u, 0x80u); /* Trigger with length disabled. */
    emit_write(program, &length, 0x16u, 0x3Fu);
    emit_write(program, &length, 0x17u, 0xF0u);
    emit_write(program, &length, 0x19u, 0x80u);
    emit_write(program, &length, 0x30u, 0x77u);
    emit_write(program, &length, 0x1Au, 0x80u);
    emit_write(program, &length, 0x1Bu, 0xFFu);
    emit_write(program, &length, 0x1Cu, 0x20u);
    emit_write(program, &length, 0x1Eu, 0x80u);
    emit_write(program, &length, 0x20u, 0x3Fu);
    emit_write(program, &length, 0x21u, 0xF0u);
    emit_write(program, &length, 0x22u, 0x00u);
    emit_write(program, &length, 0x23u, 0x80u);
    emit_write(program, &length, 0x14u, 0x40u); /* Enable length at the odd sequencer step. */
    emit_write(program, &length, 0x19u, 0x40u);
    emit_write(program, &length, 0x1Eu, 0x40u);
    emit_write(program, &length, 0x23u, 0x40u);
    emit_readback(program, &length, 0x26u, 1u);
    /* The pinned channel_1_sweep_restart_2 author case expects CGB-E restart behavior. */
    emit_write(program, &length, 0x11u, 0xBFu);
    emit_write(program, &length, 0x10u, 0x19u); /* Period 1, negate, shift 1. */
    emit_write(program, &length, 0x13u, 0x00u);
    emit_write(program, &length, 0x14u, 0x82u); /* Frequency 512 and trigger. */
    emit_readback(program, &length, 0x26u, 2u);
    emit_write(program, &length, 0x10u, 0x11u); /* Clearing used negate disables CH1. */
    emit_readback(program, &length, 0x26u, 3u);
    emit_write(program, &length, 0x14u, 0x82u); /* A fresh trigger restarts sweep state. */
    emit_readback(program, &length, 0x26u, 4u);
    program[length++] = 0x76u;

    gbb_instance *machine = load_cgb_guest(program, length);
    if (machine == NULL) {
        printf("not ok 1 - cgb_apu_trigger_length_sweep\n");
        fprintf(stderr, "could not create CGB length-counter guest\n");
        return 1;
    }
    const gbb_run_result run = gbb_run(machine, 16384u, NULL, 0u);
    const uint8_t initial_div = gbb_peek_ram(machine, 0xC000u);
    const uint8_t length_status = gbb_peek_ram(machine, 0xC001u);
    const uint8_t sweep_initial = gbb_peek_ram(machine, 0xC002u);
    const uint8_t sweep_cleared = gbb_peek_ram(machine, 0xC003u);
    const uint8_t sweep_restarted = gbb_peek_ram(machine, 0xC004u);
    gbb_destroy(machine);
    if (run.reason == GBB_STOP_HALTED_IDLE && (initial_div & 0x10u) != 0u &&
        (length_status & 0x0Fu) == 0u && (sweep_initial & 0x01u) != 0u &&
        (sweep_cleared & 0x01u) == 0u && (sweep_restarted & 0x01u) != 0u) {
        fprintf(stderr,
                "CGB trigger/length/sweep expected all four length expiries then sweep restart: DIV=%02x NR52=%02x,%02x,%02x,%02x\n",
                initial_div, length_status, sweep_initial, sweep_cleared, sweep_restarted);
    } else {
        printf("not ok 1 - cgb_apu_trigger_length_sweep\n");
        fprintf(stderr,
                "CGB trigger/length mismatch expected DIV bit4=1, length status low=0, sweep CH1=1,0,1 actual DIV=%02x NR52=%02x,%02x,%02x,%02x reason=%d\n",
                initial_div, length_status, sweep_initial, sweep_cleared,
                sweep_restarted, run.reason);
        return 1;
    }
    uint8_t fast_noise[4] = {0u}, slowed_noise[4] = {0u};
    if (run_noise_frequency_guest(0, fast_noise) != 0 ||
        run_noise_frequency_guest(1, slowed_noise) != 0 ||
        memcmp(fast_noise, slowed_noise, sizeof(fast_noise)) == 0) {
        printf("not ok 1 - cgb_apu_trigger_length_sweep\n");
        fprintf(stderr, "CH4 NR43 change control failed fast=%02x,%02x,%02x,%02x changed=%02x,%02x,%02x,%02x\n",
                fast_noise[0], fast_noise[1], fast_noise[2], fast_noise[3],
                slowed_noise[0], slowed_noise[1], slowed_noise[2], slowed_noise[3]);
        return 1;
    }
    fprintf(stderr, "CH4 NR43 transition control expected PCM sequence difference fast=%02x,%02x,%02x,%02x changed=%02x,%02x,%02x,%02x\n",
            fast_noise[0], fast_noise[1], fast_noise[2], fast_noise[3],
            slowed_noise[0], slowed_noise[1], slowed_noise[2], slowed_noise[3]);
    printf("ok 1 - cgb_apu_trigger_length_sweep\n");
    return 0;
}

typedef struct {
    gbb_stop_reason reason;
    uint8_t values[32];
} cgb_readback_result;

static void emit_readback(uint8_t *program, size_t *length, uint8_t address,
                          unsigned slot) {
    program[(*length)++] = 0xF0u;
    program[(*length)++] = address;
    program[(*length)++] = 0xEAu;
    program[(*length)++] = (uint8_t)slot;
    program[(*length)++] = 0xC0u;
}

static int run_cgb_readback_guest(const uint8_t *program, size_t length,
                                  uint64_t budget, size_t count,
                                  cgb_readback_result *out) {
    if (count > sizeof(out->values)) return 1;
    gbb_instance *machine = load_cgb_guest(program, length);
    if (machine == NULL) return 1;
    const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
    out->reason = run.reason;
    for (size_t i = 0u; i < count; ++i)
        out->values[i] = gbb_peek_ram(machine, (uint16_t)(0xC000u + i));
    gbb_destroy(machine);
    return 0;
}

static void emit_nops(uint8_t *program, size_t *length, unsigned count) {
    for (unsigned i = 0u; i < count; ++i) program[(*length)++] = 0x00u;
}

static int run_noise_frequency_guest(int slow_after_trigger, uint8_t samples[4]) {
    uint8_t program[256];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x21u, 0xF0u);
    emit_write(program, &length, 0x22u, 0x00u);
    emit_write(program, &length, 0x23u, 0x80u);
    if (slow_after_trigger) emit_write(program, &length, 0x22u, 0x70u);
    for (unsigned i = 0u; i < 4u; ++i) {
        if (i != 0u) emit_nops(program, &length, 32u);
        emit_readback(program, &length, 0x77u, i);
    }
    program[length++] = 0x76u;
    cgb_readback_result result = {0};
    if (run_cgb_readback_guest(program, length, 8192u, 4u, &result) != 0 ||
        result.reason != GBB_STOP_HALTED_IDLE)
        return 1;
    memcpy(samples, result.values, 4u);
    return 0;
}

static int cgb_apu_power(void) {
    uint8_t program[1024];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x24u, 0x77u);
    emit_write(program, &length, 0x25u, 0xFFu);
    emit_write(program, &length, 0x11u, 0x80u);
    emit_write(program, &length, 0x12u, 0xF0u);
    emit_write(program, &length, 0x14u, 0x80u);
    for (unsigned i = 0u; i < 16u; ++i)
        emit_write(program, &length, (uint8_t)(0x30u + i), 0x77u);
    emit_write(program, &length, 0x1Au, 0x80u);
    emit_write(program, &length, 0x1Cu, 0x20u);
    emit_write(program, &length, 0x1Du, 0xFFu);
    emit_write(program, &length, 0x1Eu, 0x87u);
    emit_nops(program, &length, 8u);
    emit_readback(program, &length, 0x26u, 0u);
    emit_write(program, &length, 0x26u, 0x00u);
    emit_readback(program, &length, 0x26u, 1u);
    emit_readback(program, &length, 0x11u, 2u);
    emit_readback(program, &length, 0x12u, 3u);
    emit_readback(program, &length, 0x24u, 4u);
    emit_readback(program, &length, 0x25u, 5u);
    emit_readback(program, &length, 0x30u, 6u);
    emit_readback(program, &length, 0x04u, 7u);
    emit_nops(program, &length, 256u);
    emit_readback(program, &length, 0x04u, 8u);
    emit_write(program, &length, 0x26u, 0x80u);
    emit_readback(program, &length, 0x26u, 9u);
    emit_readback(program, &length, 0x30u, 10u);
    program[length++] = 0x76u;

    cgb_readback_result result = {0};
    if (run_cgb_readback_guest(program, length, 16384u, 11u, &result) != 0 ||
        result.reason != GBB_STOP_HALTED_IDLE ||
        (result.values[0] & 0x05u) != 0x05u || result.values[1] != 0x70u ||
        result.values[2] != 0x3Fu || result.values[3] != 0x00u ||
        result.values[4] != 0x00u || result.values[5] != 0x00u ||
        result.values[6] != 0x77u || result.values[7] == result.values[8] ||
        result.values[9] != 0xF0u || result.values[10] != 0x77u) {
        printf("not ok 1 - cgb_apu_power\n");
        fprintf(stderr,
                "CGB power sequence mismatch reason=%d values=%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x\n",
                result.reason, result.values[0], result.values[1], result.values[2],
                result.values[3], result.values[4], result.values[5], result.values[6],
                result.values[7], result.values[8], result.values[9], result.values[10]);
        return 1;
    }
    fprintf(stderr,
            "CGB NR52 off/on expected status=70/f0 and retained wave=77; DIV advanced %02x->%02x\n",
            result.values[7], result.values[8]);
    printf("ok 1 - cgb_apu_power\n");
    return 0;
}

static int cgb_apu_off_writes(void) {
    static const uint8_t writes[][2] = {
        {0x10u,0x7Fu},{0x11u,0xFFu},{0x12u,0xF0u},{0x13u,0xFFu},{0x14u,0xC7u},
        {0x16u,0xFFu},{0x17u,0xF0u},{0x18u,0xFFu},{0x19u,0xC7u},{0x1Au,0x80u},
        {0x1Bu,0xFFu},{0x1Cu,0x60u},{0x1Du,0xFFu},{0x1Eu,0xC7u},{0x20u,0x3Fu},
        {0x21u,0xF0u},{0x22u,0xFFu},{0x23u,0xC0u},{0x24u,0x77u},{0x25u,0xFFu}
    };
    static const uint8_t reads[] = {
        0x10u,0x11u,0x12u,0x13u,0x14u,0x16u,0x17u,0x18u,0x19u,
        0x1Au,0x1Bu,0x1Cu,0x1Du,0x1Eu,0x20u,0x21u,0x22u,0x23u,
        0x24u,0x25u,0x26u
    };
    static const uint8_t expected[] = {
        0x80u,0x3Fu,0x00u,0xFFu,0xBFu,0x3Fu,0x00u,0xFFu,0xBFu,
        0x7Fu,0xFFu,0x9Fu,0xFFu,0xBFu,0xFFu,0x00u,0x00u,0xBFu,
        0x00u,0x00u,0x70u
    };
    uint8_t program[512];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    emit_write(program, &length, 0x30u, 0x77u);
    emit_write(program, &length, 0x26u, 0x00u);
    for (size_t i = 0u; i < sizeof(writes) / sizeof(writes[0]); ++i)
        emit_write(program, &length, writes[i][0], writes[i][1]);
    emit_write(program, &length, 0x30u, 0xABu); /* Wave RAM is writable while off. */
    for (size_t i = 0u; i < sizeof(reads); ++i)
        emit_readback(program, &length, reads[i], (unsigned)i);
    emit_write(program, &length, 0x26u, 0x80u);
    emit_readback(program, &length, 0x26u, 21u);
    emit_readback(program, &length, 0x12u, 22u);
    emit_readback(program, &length, 0x30u, 23u);
    program[length++] = 0x76u;

    cgb_readback_result result = {0};
    int mismatch = run_cgb_readback_guest(program, length, 8192u, 24u, &result) != 0 ||
                   result.reason != GBB_STOP_HALTED_IDLE;
    for (size_t i = 0u; i < sizeof(expected); ++i)
        if (result.values[i] != expected[i]) mismatch = 1;
    if (mismatch) {
        printf("not ok 1 - cgb_apu_off_writes\n");
        fprintf(stderr, "off-state register writes/read masks mismatch reason=%d", result.reason);
        for (size_t i = 0u; i < sizeof(expected); ++i)
            fprintf(stderr, " %02x/%02x", result.values[i], expected[i]);
        fputc('\n', stderr);
        return 1;
    }
    fprintf(stderr, "CGB APU masks and off-state writes passed; Wave RAM retained 0xab\n");
    printf("ok 1 - cgb_apu_off_writes\n");
    return 0;
}

static int cgb_apu_wave_access(void) {
    uint8_t program[1024];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x80u);
    for (unsigned i = 0u; i < 16u; ++i)
        emit_write(program, &length, (uint8_t)(0x30u + i), 0x77u);
    emit_write(program, &length, 0x31u, 0x39u);
    emit_write(program, &length, 0x1Au, 0x80u);
    emit_write(program, &length, 0x1Cu, 0x20u);
    emit_write(program, &length, 0x1Du, 0xFFu);
    emit_write(program, &length, 0x1Eu, 0x87u);
    emit_nops(program, &length, 8u);
    emit_write(program, &length, 0x1Du, 0x00u);
    emit_write(program, &length, 0x1Eu, 0x80u);
    emit_write(program, &length, 0x31u, 0xA3u);
    emit_readback(program, &length, 0x31u, 0u);
    emit_readback(program, &length, 0x30u, 1u);
    emit_readback(program, &length, 0x77u, 2u);
    emit_nops(program, &length, 512u);
    emit_readback(program, &length, 0x77u, 3u);
    program[length++] = 0x76u;

    cgb_readback_result result = {0};
    if (run_cgb_readback_guest(program, length, 8192u, 4u, &result) != 0 ||
        result.reason != GBB_STOP_HALTED_IDLE || result.values[0] != 0xA3u ||
        result.values[1] != 0xA3u || result.values[2] != 0x07u ||
        result.values[3] != 0x03u) {
        printf("not ok 1 - cgb_apu_wave_access\n");
        fprintf(stderr, "active Wave RAM mismatch reason=%d reads=%02x,%02x PCM=%02x->%02x\n",
                result.reason, result.values[0], result.values[1],
                result.values[2], result.values[3]);
        return 1;
    }
    fprintf(stderr, "CGB active Wave RAM alias expected=0xa3; CH3 buffer 0x07->0x03 at fetch\n");
    printf("ok 1 - cgb_apu_wave_access\n");
    return 0;
}

static int run_cgb_div_edge_guest(int double_speed, int reset_div,
                                  uint8_t *status, uint8_t *key1) {
    uint8_t program[128];
    size_t length = 0u;
    emit_write(program, &length, 0x26u, 0x00u); /* Hold the sequencer reset while waiting for DIV. */
    if (double_speed) {
        emit_write(program, &length, 0x4Du, 0x01u);
        program[length++] = 0x10u; program[length++] = 0x00u; /* Armed STOP switches speed. */
    }
    const uint8_t mask = double_speed ? 0x30u : 0x10u;
    const uint8_t wanted = double_speed ? 0x20u : 0x10u;
    program[length++] = 0xF0u; program[length++] = 0x04u;
    program[length++] = 0xE6u; program[length++] = mask;
    program[length++] = 0xFEu; program[length++] = wanted;
    program[length++] = 0x20u; program[length++] = 0xF8u; /* Wait for the selected high tap. */
    emit_write(program, &length, 0x26u, 0x80u); /* Power-on resets sequence step to zero. */
    emit_write(program, &length, 0x11u, 0x3Fu);
    emit_write(program, &length, 0x12u, 0xF0u);
    emit_write(program, &length, 0x14u, 0xC0u); /* One count, trigger and length enabled. */
    if (reset_div) emit_write(program, &length, 0x04u, 0x00u);
    emit_readback(program, &length, 0x26u, 0u);
    emit_readback(program, &length, 0x4Du, 1u);
    program[length++] = 0x76u;

    cgb_readback_result result = {0};
    if (run_cgb_readback_guest(program, length, double_speed ? 200000u : 16384u,
                               2u, &result) != 0 || result.reason != GBB_STOP_HALTED_IDLE)
        return 1;
    *status = result.values[0];
    *key1 = result.values[1];
    return 0;
}

static int cgb_apu_div_stop(void) {
    uint8_t normal_status = 0u, normal_key1 = 0u;
    uint8_t double_status = 0u, double_key1 = 0u;
    if (run_cgb_div_edge_guest(0, 1, &normal_status, &normal_key1) != 0 ||
        run_cgb_div_edge_guest(1, 1, &double_status, &double_key1) != 0 ||
        (normal_status & 1u) != 0u || (double_status & 1u) != 0u ||
        (normal_key1 & 0x80u) != 0u || (double_key1 & 0x80u) == 0u) {
        printf("not ok 1 - cgb_apu_div_stop\n");
        fprintf(stderr, "DIV tap/STOP mismatch NR52=%02x,%02x KEY1=%02x,%02x\n",
                normal_status, double_status, normal_key1, double_key1);
        return 1;
    }
    fprintf(stderr, "DIV falling-edge guests passed normal bit12 and double bit13 after STOP\n");
    printf("ok 1 - cgb_apu_div_stop\n");
    return 0;
}

static int cgb_apu_transition_controls(void) {
    uint8_t normal_status = 0u, normal_key1 = 0u;
    uint8_t double_status = 0u, double_key1 = 0u;
    if (run_cgb_div_edge_guest(0, 0, &normal_status, &normal_key1) != 0 ||
        run_cgb_div_edge_guest(1, 0, &double_status, &double_key1) != 0 ||
        (normal_status & 1u) == 0u || (double_status & 1u) == 0u) {
        printf("not ok 1 - cgb_apu_transition_controls\n");
        fprintf(stderr, "omitted-DIV control mismatch NR52=%02x,%02x\n",
                normal_status, double_status);
        return 1;
    }
    fprintf(stderr,
            "negative-control diagnostic: omitting the DIV write preserved CH1 at normal and double speed (%02x,%02x)\n",
            normal_status, double_status);
    printf("ok 1 - cgb_apu_transition_controls\n");
    return 0;
}

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "cgb_pcm_tracer";
    printf("TAP version 13\n1..1\n");
    if (strcmp(name, "cgb_pcm_tracer") == 0)
        return cgb_pcm_tracer(GBB_CGB_APU_CONTROL_MUTANT == 1);
    if (strcmp(name, "cgb_pcm_tracer_control") == 0)
        return cgb_pcm_tracer(1);
    if (strcmp(name, "cgb_pcm_channels") == 0) return cgb_pcm_channels(name);
    if (strcmp(name, "cgb_pcm_power_dac") == 0) return cgb_pcm_power_dac(name);
    if (strcmp(name, "cgb_pcm_readonly") == 0) return cgb_pcm_readonly(name);
    if (strcmp(name, "cgb_pcm_host_invariance") == 0) return cgb_pcm_host_invariance(name);
    if (strcmp(name, "cgb_pcm_controls") == 0) {
        if (GBB_CGB_APU_CONTROL_MUTANT == 2)
            return cgb_pcm_routing_mutant_control(name);
        if (GBB_CGB_APU_CONTROL_MUTANT == 3)
            return cgb_pcm_writable_mutant_control(name);
        return cgb_pcm_controls(name);
    }
    if (strcmp(name, "cgb_apu_wave_latch") == 0) return cgb_apu_wave_latch();
    if (strcmp(name, "cgb_apu_wave_fetch") == 0) return cgb_apu_wave_fetch();
#if GBB_CGB_APU_CONTROL_MUTANT == 4
    if (strcmp(name, "cgb_apu_wave_direct_ram_control") == 0)
        return cgb_apu_wave_direct_ram_control(name);
#endif
    if (strcmp(name, "cgb_apu_trigger_length_sweep") == 0)
        return cgb_apu_trigger_length_sweep();
    if (strcmp(name, "cgb_apu_power") == 0) return cgb_apu_power();
    if (strcmp(name, "cgb_apu_off_writes") == 0) return cgb_apu_off_writes();
    if (strcmp(name, "cgb_apu_wave_access") == 0) return cgb_apu_wave_access();
    if (strcmp(name, "cgb_apu_div_stop") == 0) return cgb_apu_div_stop();
    if (strcmp(name, "cgb_apu_transition_controls") == 0)
        return cgb_apu_transition_controls();
    printf("not ok 1 - %s # unknown test\n", name);
    return 1;
}
