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
        emit_write(program, &length, 0x1Du, 0x00u);
        emit_write(program, &length, 0x1Eu, 0x80u);
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
    printf("not ok 1 - %s # unknown test\n", name);
    return 1;
}
