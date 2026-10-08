#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", case_name); fflush(stdout); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS() do { printf("ok 1 - %s\n", case_name); return 0; } while (0)

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static gbb_instance *load_program(const uint8_t *program, size_t length) {
    uint8_t *rom = calloc(1u, 32768u);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100u, program, length);
    fix_checksum(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768u) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static gbb_instance *load_nops(void) {
    static const uint8_t nop = 0x00u;
    return load_program(&nop, 1u);
}

static int audio_tracer(const char *case_name) {
    static const uint8_t program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu,
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu,
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu,
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu,
        0x18u, 0xFEu
    };
    gbb_instance *machine = load_program(program, sizeof(program));
    REQUIRE(machine != NULL);
    gbb_test_bus_event events[32] = {{0}};
    gbb_test_observer_set(machine, events, 32u);
    gbb_audio_frame frames[804] = {{0}};
    size_t count = 0u;
    const uint64_t elapsed = UINT64_C(140448);
    const gbb_run_result result = gbb_run_audio(machine, elapsed, frames,
                                                804u, &count);
    REQUIRE(result.reason == GBB_STOP_BUDGET);
    REQUIRE(result.consumed_half_dots == elapsed);
    REQUIRE(count == (size_t)((elapsed * UINT64_C(48000)) / UINT64_C(8388608)));
    REQUIRE(count == 803u);

    uint64_t trigger_time = UINT64_MAX;
    const size_t event_count = gbb_test_observer_count(machine);
    for (size_t i = 0u; i < event_count; ++i) {
        if (events[i].address == 0xFF14u && events[i].access == 2u &&
            events[i].value == 0x87u) {
            trigger_time = events[i].time_half_dots;
            break;
        }
    }
    REQUIRE(trigger_time != UINT64_MAX);
    unsigned high_samples = 0u;
    unsigned transitions = 0u;
    int16_t previous = frames[0].left;
    for (size_t i = 0u; i < count; ++i) {
        const uint64_t sample_time =
            (((uint64_t)(i + 1u) * UINT64_C(8388608)) + UINT64_C(47999)) /
            UINT64_C(48000);
        int16_t expected = 0;
        if (sample_time > trigger_time) {
            const uint64_t pulse_phase =
                ((sample_time - trigger_time) / UINT64_C(1024)) & 7u;
            if (((0x87u >> pulse_phase) & 1u) != 0u) expected = 14336;
        }
        REQUIRE(frames[i].left == expected && frames[i].right == expected);
        if (expected != 0) ++high_samples;
        if (i != 0u && frames[i].left != previous) ++transitions;
        previous = frames[i].left;
    }
    REQUIRE(high_samples > 100u && high_samples < count);
    REQUIRE(transitions > 20u);
    gbb_destroy(machine);
    PASS();
}

static int audio_capacity(const char *case_name) {
    size_t count = SIZE_MAX;
    gbb_instance *zero = load_nops();
    REQUIRE(zero != NULL);
    gbb_run_result result = gbb_run_audio(zero, 8u, NULL, 0u, &count);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 8u);
    REQUIRE(count == 0u);
    gbb_destroy(zero);

    gbb_instance *short_output = load_nops();
    gbb_instance *baseline = load_nops();
    REQUIRE(short_output != NULL && baseline != NULL);
    REQUIRE(gbb_run(short_output, 344u, NULL, 0u).consumed_half_dots == 344u);
    REQUIRE(gbb_run(baseline, 344u, NULL, 0u).consumed_half_dots == 344u);
    struct {
        uint32_t before;
        gbb_audio_frame frame;
        uint32_t after;
    } guarded = {0xA55AA55Au, {0, 0}, 0x5AA55AA5u};
    count = 0u;
    result = gbb_run_audio(short_output, 400u, &guarded.frame, 1u, &count);
    REQUIRE(result.reason == GBB_STOP_OUTPUT_FULL);
    REQUIRE(result.consumed_half_dots > 0u && result.consumed_half_dots < 400u);
    REQUIRE(count == 1u);
    REQUIRE(guarded.before == 0xA55AA55Au && guarded.after == 0x5AA55AA5u);
    gbb_trace_record actual = {0}, expected = {0};
    REQUIRE(gbb_run(short_output, 8u, &actual, 1u).consumed_half_dots == 8u);
    REQUIRE(gbb_run(baseline, result.consumed_half_dots, NULL, 0u)
                .consumed_half_dots == result.consumed_half_dots);
    REQUIRE(gbb_run(baseline, 8u, &expected, 1u).consumed_half_dots == 8u);
    REQUIRE(actual.time_half_dots == expected.time_half_dots &&
            actual.pc == expected.pc && actual.a == expected.a &&
            actual.f == expected.f && actual.sp == expected.sp);

    gbb_instance *exact = load_nops();
    REQUIRE(exact != NULL);
    REQUIRE(gbb_run(exact, 344u, NULL, 0u).consumed_half_dots == 344u);
    gbb_audio_frame one_frame = {0, 0};
    count = 0u;
    result = gbb_run_audio(exact, 8u, &one_frame, 1u, &count);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 8u);
    REQUIRE(count == 1u);
    gbb_destroy(exact);
    gbb_destroy(short_output);
    gbb_destroy(baseline);
    PASS();
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const char *case_name = argv[1];
    puts("1..1");
    if (strcmp(case_name, "audio_tracer") == 0) return audio_tracer(case_name);
    if (strcmp(case_name, "audio_capacity") == 0) return audio_capacity(case_name);
    return 2;
}
