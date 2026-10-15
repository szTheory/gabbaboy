#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ROM_BYTES 32768u
#define RESULT_ADDRESS 0xC000u
#define RESULT_CODE_ADDRESS 0xCFFEu
#define RUN_SLICE UINT64_C(2048)
#define RUN_BUDGET UINT64_C(1404480)
#define MAX_RUN_CALLS 4096u

typedef struct {
    const char *name;
    const char *rom_sha256;
    const uint8_t *expected_results;
    size_t result_count;
} apu_case;

static const uint8_t channel_3_first_sample_expected[] = {
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x0Eu, 0x0Eu, 0x0Eu
};

static const apu_case CHANNEL_3_FIRST_SAMPLE = {
    "apu/channel_3/channel_3_first_sample",
    "464b7139b6c2147fa0984006d32507559972404f538e53408369c1c337b1b6e7",
    channel_3_first_sample_expected,
    sizeof(channel_3_first_sample_expected)
};

static int compare_results(const uint8_t *expected, const uint8_t *observed,
                           size_t count) {
    if (expected == NULL || observed == NULL || count == 0u) return 0;
    for (size_t i = 0u; i < count; ++i)
        if (expected[i] != observed[i]) return 0;
    return 1;
}

static int read_rom(const char *path, uint8_t rom[ROM_BYTES]) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "samesuite-apu fixture: cannot open %s\n", path);
        return 0;
    }
    const size_t count = fread(rom, 1u, ROM_BYTES, file);
    const int extra = fgetc(file);
    const int read_error = ferror(file);
    fclose(file);
    if (read_error || count != ROM_BYTES || extra != EOF) {
        fprintf(stderr,
                "samesuite-apu fixture: expected exactly %u bytes actual=%zu\n",
                ROM_BYTES, count);
        return 0;
    }
    return 1;
}

static int rom_matches(const uint8_t rom[ROM_BYTES], const char *expected_sha256) {
    char actual[65];
    gbb_accept_sha256_hex(rom, ROM_BYTES, actual);
    if (strcmp(actual, expected_sha256) == 0) return 1;
    fprintf(stderr, "samesuite-apu ROM SHA-256 mismatch expected=%s actual=%s\n",
            expected_sha256, actual);
    return 0;
}

static int run_case(const apu_case *test, const char *rom_path,
                    int corrupt_direct_sample, int require_detected_mutation) {
    uint8_t rom[ROM_BYTES];
    uint8_t observed[144u] = {0u};
    gbb_instance *machine = NULL;
    uint64_t elapsed = 0u;
    unsigned run_calls = 0u;
    int terminal = 0;

    if (!read_rom(rom_path, rom) || !rom_matches(rom, test->rom_sha256)) return 1;
    if (test->result_count == 0u || test->result_count > sizeof(observed)) {
        fprintf(stderr,
                "samesuite-apu result-count: unsupported count=%zu limit=%zu\n",
                test->result_count, sizeof(observed));
        return 1;
    }
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK || machine == NULL) {
        fprintf(stderr, "samesuite-apu create: CGB-CPU-E failed\n");
        gbb_destroy(machine);
        return 1;
    }
    if (gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        fprintf(stderr, "samesuite-apu load: admitted ROM rejected\n");
        gbb_destroy(machine);
        return 1;
    }

    while (elapsed < RUN_BUDGET && run_calls < MAX_RUN_CALLS) {
        const uint64_t remaining = RUN_BUDGET - elapsed;
        const uint64_t slice = remaining < RUN_SLICE ? remaining : RUN_SLICE;
        const gbb_run_result run = gbb_run(machine, slice, NULL, 0u);
        ++run_calls;
        if (run.consumed_half_dots == 0u || run.consumed_half_dots > slice) {
            fprintf(stderr,
                    "samesuite-apu run: invalid progress reason=%d consumed=%llu\n",
                    (int)run.reason, (unsigned long long)run.consumed_half_dots);
            gbb_destroy(machine);
            return 1;
        }
        elapsed += run.consumed_half_dots;
        if (run.reason == GBB_STOP_HALTED_IDLE) {
            terminal = 1;
            break;
        }
        if (run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_OUTPUT_FULL) {
            fprintf(stderr,
                    "samesuite-apu run: unexpected stop=%d elapsed=%llu\n",
                    (int)run.reason, (unsigned long long)elapsed);
            gbb_destroy(machine);
            return 1;
        }
    }
    if (!terminal) {
        fprintf(stderr,
                "samesuite-apu run: terminal guest verdict not reached budget=%llu calls=%u\n",
                (unsigned long long)RUN_BUDGET, run_calls);
        gbb_destroy(machine);
        return 1;
    }

    for (size_t i = 0u; i < test->result_count; ++i)
        observed[i] = gbb_peek_ram(machine, (uint16_t)(RESULT_ADDRESS + i));
    if (corrupt_direct_sample) observed[0] ^= 0x01u;
    const uint8_t result_code = gbb_peek_ram(machine, RESULT_CODE_ADDRESS);
    const int values_match = compare_results(test->expected_results, observed,
                                             test->result_count);
    if (result_code != (uint8_t)'P' && result_code != (uint8_t)'F') {
        fprintf(stderr,
                "samesuite-apu guest-result case=%s invalid-terminal=%02x terminal=1 elapsed_half_dots=%llu run_calls=%u\n",
                test->name, result_code, (unsigned long long)elapsed, run_calls);
        gbb_destroy(machine);
        return 1;
    }
    if (require_detected_mutation && values_match) {
        fprintf(stderr,
                "samesuite-apu control: direct-ram-result-mutation-undetected case=%s\n",
                test->name);
        gbb_destroy(machine);
        return 1;
    }

    fprintf(stderr,
            "samesuite-apu guest-result case=%s author_expectation=P observed=%c evaluator_disposition=not-qualified terminal=1 elapsed_half_dots=%llu run_calls=%u assertions=%zu assertion_set=%s test_sample_corruption=%s\n",
            test->name, (char)result_code, (unsigned long long)elapsed,
            run_calls, test->result_count,
            values_match ? "match" : "mismatch",
            corrupt_direct_sample ? "enabled" : "disabled");
    for (size_t i = 0u; i < test->result_count; ++i) {
        fprintf(stderr,
                "samesuite-apu assertion case=%s id=result-%03zu author_expected=%02x observed=%02x status=%s\n",
                test->name, i, test->expected_results[i], observed[i],
                test->expected_results[i] == observed[i] ? "match" : "mismatch");
    }
    gbb_destroy(machine);
    /* A tracer records a bounded terminal observation. Qualification and
     * expected-failure matching happen in the separate disposition gate. */
    return 0;
}

static int tracer_controls(const char *rom_path) {
    uint8_t rom[ROM_BYTES];
    uint8_t mutated[sizeof(channel_3_first_sample_expected)];
    memcpy(mutated, channel_3_first_sample_expected, sizeof(mutated));
    mutated[0] ^= 0x01u;
    if (compare_results(channel_3_first_sample_expected, mutated,
                        sizeof(mutated)) != 0) {
        fprintf(stderr,
                "samesuite-apu control: mutated result accepted expected=00 observed=01\n");
        return 1;
    }
    if (!read_rom(rom_path, rom)) return 1;
    rom[0x150u] ^= 0x01u;
    if (rom_matches(rom, CHANNEL_3_FIRST_SAMPLE.rom_sha256)) {
        fprintf(stderr, "samesuite-apu control: mutated ROM digest accepted\n");
        return 1;
    }
    const int guest_mutation_detected = run_case(&CHANNEL_3_FIRST_SAMPLE,
                                                rom_path, 1, 1);
    if (guest_mutation_detected != 0) return guest_mutation_detected;
    fprintf(stderr,
            "samesuite-apu controls pass changed-result=detected direct-ram-result-mutation=detected changed-rom=detected\n");
    return 0;
}

int main(int argc, char **argv) {
    int result = 2;
    const char *name = argc > 1 ? argv[1] : "";
    puts("TAP version 13");
    puts("1..1");
    if (strcmp(name, "--tracer") == 0 && argc == 3)
        result = run_case(&CHANNEL_3_FIRST_SAMPLE, argv[2], 0, 0);
    else if (strcmp(name, "--controls") == 0 && argc == 3)
        result = tracer_controls(argv[2]);
    else {
        fprintf(stderr, "samesuite-apu: invalid command\n");
        puts("not ok 1 - cgb_samesuite_apu command");
        return 2;
    }
    if (result == 0) {
        puts(strcmp(name, "--tracer") == 0
                 ? "ok 1 - tracer recorded terminal guest observation"
                 : "ok 1 - cgb_samesuite_apu_tracer_controls");
        return 0;
    }
    puts(strcmp(name, "--tracer") == 0
             ? "not ok 1 - cgb_samesuite_apu_tracer"
             : "not ok 1 - cgb_samesuite_apu_tracer_controls");
    return result;
}
