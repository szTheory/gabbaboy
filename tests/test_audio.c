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
extern void gbb_test_audio_kernel(gbb_instance *, const int32_t *, const int32_t *,
                                  size_t, gbb_audio_frame *);
extern void gbb_test_audio_edge(gbb_instance *, int32_t, int32_t, unsigned,
                                gbb_audio_frame *);

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

static uint64_t hash_frames(uint64_t hash, const gbb_audio_frame *frames,
                            size_t count) {
    for (size_t i = 0u; i < count; ++i) {
        const uint16_t values[2] = {(uint16_t)frames[i].left,
                                    (uint16_t)frames[i].right};
        for (unsigned channel = 0u; channel < 2u; ++channel) {
            hash ^= (uint8_t)values[channel];
            hash *= UINT64_C(1099511628211);
            hash ^= (uint8_t)(values[channel] >> 8);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
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
        REQUIRE(frames[i].left == frames[i].right);
        REQUIRE(frames[i].left >= INT16_MIN && frames[i].left <= INT16_MAX);
        if (frames[i].left != 0) ++high_samples;
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
    gbb_audio_frame expected_frames[8] = {{0}}, retry_frames[8] = {{0}};
    size_t expected_count = 0u, retry_count = 0u;
    gbb_run_result expected_run = gbb_run_audio(baseline, 400u, expected_frames,
                                                8u, &expected_count);
    REQUIRE(expected_run.reason == GBB_STOP_BUDGET &&
            expected_run.consumed_half_dots == 400u);
    gbb_run_result retry_run = gbb_run_audio(short_output, 400u - result.consumed_half_dots,
                                             retry_frames, 7u, &retry_count);
    REQUIRE(retry_run.reason == GBB_STOP_BUDGET &&
            retry_run.consumed_half_dots == 400u - result.consumed_half_dots);
    REQUIRE(count + retry_count == expected_count);
    REQUIRE(memcmp(&guarded.frame, expected_frames, sizeof(guarded.frame)) == 0);
    REQUIRE(memcmp(retry_frames, expected_frames + 1u,
                   retry_count * sizeof(*retry_frames)) == 0);
    gbb_trace_record actual = {0}, expected = {0};
    REQUIRE(gbb_run(short_output, 8u, &actual, 1u).consumed_half_dots == 8u);
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

static int audio_signal(const char *case_name) {
    /* Independent authored references: unit impulse, DC step, and 1/8-duty
     * periodic square wave. Inputs are signed Q15 mixer levels. */
    static const int32_t impulse[16] = {16384};
    static const int32_t step[16] = {
        0, 0, 0, 0, 16384, 16384, 16384, 16384,
        16384, 16384, 16384, 16384, 16384, 16384, 16384, 16384
    };
    static const int32_t periodic[16] = {
        16384, 0, 0, 0, 0, 0, 0, 0,
        16384, 0, 0, 0, 0, 0, 0, 0
    };
    int32_t alternating[4096] = {0};
    for (size_t i = 2048u; i < 4096u; ++i)
        alternating[i] = (i & 1u) == 0u ? 16384 : -16384;
    gbb_instance *machine = load_nops();
    REQUIRE(machine != NULL);
    gbb_audio_frame output[4096] = {{0}};
    uint64_t digest = UINT64_C(14695981039346656037);
    gbb_test_audio_kernel(machine, impulse, impulse, 16u, output);
    digest = hash_frames(digest, output, 16u);
    int32_t impulse_peak = 0;
    for (size_t i = 0; i < 16u; ++i) {
        int32_t value = output[i].left;
        if (value < 0) value = -value;
        if (value > impulse_peak) impulse_peak = value;
        REQUIRE(output[i].left == output[i].right);
    }
    REQUIRE(impulse_peak <= 16384);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    gbb_test_audio_kernel(machine, step, step, 16u, output);
    digest = hash_frames(digest, output, 16u);
    REQUIRE(output[0].left == 0 && output[0].right == 0);
    REQUIRE(output[15].left == output[15].right);
    REQUIRE(output[15].left > 0 && output[15].left <= 16384);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    gbb_test_audio_kernel(machine, periodic, periodic, 16u, output);
    digest = hash_frames(digest, output, 16u);
    int32_t periodic_peak = 0;
    for (size_t i = 0; i < 16u; ++i) {
        int32_t value = output[i].left;
        if (value < 0) value = -value;
        if (value > periodic_peak) periodic_peak = value;
    }
    REQUIRE(periodic_peak <= 16384);
    REQUIRE(periodic_peak > 1000);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    gbb_test_audio_kernel(machine, alternating, alternating, 4096u, output);
    digest = hash_frames(digest, output, 4096u);
    for (size_t i = 4080u; i < 4096u; ++i) {
        REQUIRE(output[i].left >= -32 && output[i].left <= 32);
        REQUIRE(output[i].right >= -32 && output[i].right <= 32);
    }
    printf("# PCM reference digest (FNV-1a 64): %016llx\n",
           (unsigned long long)digest);
    gbb_destroy(machine);
    PASS();
}

static int audio_fractional_edges(const char *case_name) {
    gbb_instance *machines[3] = {load_nops(), load_nops(), load_nops()};
    REQUIRE(machines[0] != NULL && machines[1] != NULL && machines[2] != NULL);
    gbb_audio_frame frames[3] = {{0}};
    gbb_test_audio_edge(machines[0], 12000, 12000, 0u, &frames[0]);
    gbb_test_audio_edge(machines[1], 12000, 12000, 3u, &frames[1]);
    gbb_test_audio_edge(machines[2], 12000, 12000, 7u, &frames[2]);
    REQUIRE(frames[0].left > frames[1].left && frames[1].left > frames[2].left);
    REQUIRE(frames[0].left == frames[0].right && frames[1].left == frames[1].right &&
            frames[2].left == frames[2].right);
    for (unsigned i = 0u; i < 3u; ++i) gbb_destroy(machines[i]);
    PASS();
}

static int audio_partition(const char *case_name) {
    static const uint8_t program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu, 0x3Eu, 0x80u,
        0xEAu, 0x11u, 0xFFu, 0x3Eu, 0xF0u, 0xEAu, 0x13u,
        0xFFu, 0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu, 0x18u, 0xFEu
    };
    const uint64_t total = 140448u;
    gbb_instance *whole = load_program(program, sizeof(program));
    gbb_instance *split = load_program(program, sizeof(program));
    gbb_instance *many = load_program(program, sizeof(program));
    REQUIRE(whole != NULL && split != NULL && many != NULL);
    gbb_audio_frame a[804] = {{0}}, b[804] = {{0}}, c[804] = {{0}};
    size_t na = 0u, nb = 0u, nc = 0u, whole_count = 0u;
    REQUIRE(gbb_run_audio(whole, total, a, 804u, &whole_count).consumed_half_dots == total);
    gbb_run_result r = gbb_run_audio(split, total / 2u, b, 804u, &nb);
    REQUIRE(r.consumed_half_dots == total / 2u);
    r = gbb_run_audio(split, total - total / 2u, b + nb, 804u - nb, &nc);
    REQUIRE(r.consumed_half_dots == total - total / 2u);
    nb += nc;
    uint64_t remaining = total;
    nc = 0u;
    while (remaining != 0u) {
        uint64_t part = remaining > 792u ? 792u : remaining;
        size_t emitted = 0u;
        r = gbb_run_audio(many, part, c + nc, 804u - nc, &emitted);
        REQUIRE(r.consumed_half_dots == part);
        nc += emitted;
        remaining -= part;
    }
    REQUIRE(whole_count == nb && nb == nc);
    REQUIRE(memcmp(a, b, whole_count * sizeof(*a)) == 0);
    REQUIRE(memcmp(a, c, whole_count * sizeof(*a)) == 0);
    printf("# guest PCM digest (FNV-1a 64): %016llx\n",
           (unsigned long long)hash_frames(UINT64_C(14695981039346656037), a,
                                           whole_count));
    gbb_destroy(whole); gbb_destroy(split); gbb_destroy(many);
    PASS();
}

static int audio_filter(const char *case_name) {
    gbb_instance *machine = load_nops();
    REQUIRE(machine != NULL);
    int32_t step[256];
    int32_t zero[256] = {0};
    gbb_audio_frame output[256] = {{0}};
    for (size_t i = 0; i < 256u; ++i) step[i] = 16384;
    gbb_test_audio_kernel(machine, step, step, 256u, output);
    REQUIRE(output[0].left > 0);
    REQUIRE(output[255].left >= 6000 && output[255].left <= 7000);
    REQUIRE(output[255].left == output[255].right);
    REQUIRE(gbb_reset(machine) == GBB_OK);
    memset(output, 0, sizeof(output));
    gbb_test_audio_kernel(machine, step, step, 1u, output);
    REQUIRE(output[0].left > 0);
    gbb_test_audio_kernel(machine, zero, zero, 32u, output + 1u);
    REQUIRE(output[32].left < output[0].left);
    gbb_destroy(machine);
    PASS();
}

static int audio_api_edges(const char *case_name) {
    gbb_instance *overlap_machine = load_nops();
    gbb_instance *overflow_machine = load_nops();
    gbb_instance *overlap_baseline = load_nops();
    gbb_instance *overflow_baseline = load_nops();
    REQUIRE(overlap_machine != NULL && overflow_machine != NULL &&
            overlap_baseline != NULL && overflow_baseline != NULL);
    union { size_t count; gbb_audio_frame frame; } overlap = {.count = SIZE_MAX};
    gbb_run_result result = gbb_run_audio(overlap_machine, 8u, &overlap.frame,
                                          1u, &overlap.count);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u);
    REQUIRE(overlap.count == 0u);

    gbb_audio_frame guard = {1234, -4321};
    size_t count = SIZE_MAX;
    result = gbb_run_audio(overflow_machine, 8u, &guard, SIZE_MAX, &count);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u);
    REQUIRE(count == 0u && guard.left == 1234 && guard.right == -4321);
    result = gbb_run_audio(overflow_machine, 8u, NULL, 1u, &count);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u);
    REQUIRE(count == 0u);
    result = gbb_run_audio(overflow_machine, 8u, &guard, 0u, NULL);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u);
    REQUIRE(guard.left == 1234 && guard.right == -4321);

    gbb_trace_record actual = {0}, expected = {0};
    REQUIRE(gbb_run(overlap_machine, 8u, &actual, 1u).consumed_half_dots == 8u);
    REQUIRE(gbb_run(overlap_baseline, 8u, &expected, 1u).consumed_half_dots == 8u);
    REQUIRE(actual.pc == expected.pc && actual.time_half_dots == expected.time_half_dots);
    REQUIRE(gbb_run(overflow_machine, 8u, &actual, 1u).consumed_half_dots == 8u);
    REQUIRE(gbb_run(overflow_baseline, 8u, &expected, 1u).consumed_half_dots == 8u);
    REQUIRE(actual.pc == expected.pc && actual.time_half_dots == expected.time_half_dots);
    gbb_destroy(overlap_machine); gbb_destroy(overflow_machine);
    gbb_destroy(overlap_baseline); gbb_destroy(overflow_baseline);
    PASS();
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const char *case_name = argv[1];
    puts("1..1");
    if (strcmp(case_name, "audio_tracer") == 0) return audio_tracer(case_name);
    if (strcmp(case_name, "audio_capacity") == 0) return audio_capacity(case_name);
    if (strcmp(case_name, "audio_signal") == 0) return audio_signal(case_name);
    if (strcmp(case_name, "audio_fractional_edges") == 0) return audio_fractional_edges(case_name);
    if (strcmp(case_name, "audio_partition") == 0) return audio_partition(case_name);
    if (strcmp(case_name, "audio_filter") == 0) return audio_filter(case_name);
    if (strcmp(case_name, "audio_api_edges") == 0) return audio_api_edges(case_name);
    return 2;
}
