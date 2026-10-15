#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef GBB_CGB_APU_CONTROL_MUTANT
#define GBB_CGB_APU_CONTROL_MUTANT 0
#endif

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

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "cgb_pcm_tracer";
    printf("TAP version 13\n1..1\n");
    if (strcmp(name, "cgb_pcm_tracer") == 0)
        return cgb_pcm_tracer(GBB_CGB_APU_CONTROL_MUTANT != 0);
    if (strcmp(name, "cgb_pcm_tracer_control") == 0)
        return cgb_pcm_tracer(1);
    printf("not ok 1 - %s # unknown test\n", name);
    return 1;
}
