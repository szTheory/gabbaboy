#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ROM_BYTES 32768u
#define QUALIFICATION_INPUT_MAX_BYTES (4u * 1024u * 1024u)
#define RESULT_ADDRESS 0xC000u
#define RESULT_CODE_ADDRESS 0xCFFEu
#define RUN_SLICE UINT64_C(2048)
#define RUN_BUDGET UINT64_C(33554432)
#define MAX_RUN_CALLS 16384u

typedef struct {
    const char *name;
    const char *rom_sha256;
    uint16_t result_address;
    const uint8_t *expected_results;
    size_t result_count;
    const char *fixture_file;
    const char *expected_disposition;
    const char *expected_signature;
} apu_case;

static const uint8_t channel_3_first_sample_expected[] = {
    0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x0Eu, 0x0Eu, 0x0Eu
};

static const apu_case CHANNEL_3_FIRST_SAMPLE = {
    "apu/channel_3/channel_3_first_sample",
    "464b7139b6c2147fa0984006d32507559972404f538e53408369c1c337b1b6e7",
    RESULT_ADDRESS,
    channel_3_first_sample_expected,
    sizeof(channel_3_first_sample_expected),
    "apu/channel_3/channel_3_first_sample.gb",
    NULL,
    NULL
};

#include "samesuite_apu_cases.h"

static int run_case(const apu_case *test, const char *rom_path,
                    int corrupt_direct_sample, int require_detected_mutation,
                    const char *expected_disposition,
                    const char *expected_signature);

static int compare_results(const uint8_t *expected, const uint8_t *observed,
                           size_t count) {
    if (expected == NULL || observed == NULL || count == 0u) return 0;
    for (size_t i = 0u; i < count; ++i)
        if (expected[i] != observed[i]) return 0;
    return 1;
}

static int result_signature(const apu_case *test, uint8_t guest_result,
                            const uint8_t *observed, char signature[65]) {
    char input[64u + 144u * 40u];
    size_t used = 0u;
    int written = snprintf(input, sizeof(input),
                           "samesuite-apu-observation-v1\n%s\n%c\n",
                           test->name, (char)guest_result);
    if (written < 0 || (size_t)written >= sizeof(input)) return 0;
    used = (size_t)written;
    for (size_t i = 0u; i < test->result_count; ++i) {
        written = snprintf(input + used, sizeof(input) - used,
                           "result-%03zu|%02x|%02x\n", i,
                           test->expected_results[i], observed[i]);
        if (written < 0 || (size_t)written >= sizeof(input) - used) return 0;
        used += (size_t)written;
    }
    gbb_accept_sha256_hex((const uint8_t *)input, used, signature);
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

static int file_matches_sha256(const char *path, const char *expected_sha256) {
    uint8_t buffer[4096u];
    gbb_accept_sha256_ctx digest;
    char actual[65];
    FILE *file = fopen(path, "rb");
    size_t total = 0u;
    if (file == NULL) {
        fprintf(stderr, "samesuite-apu suite: cannot open qualification input %s\n", path);
        return 0;
    }
    gbb_accept_sha256_init(&digest);
    for (;;) {
        const size_t count = fread(buffer, 1u, sizeof(buffer), file);
        if (count > QUALIFICATION_INPUT_MAX_BYTES - total) {
            fprintf(stderr,
                    "samesuite-apu suite: qualification input exceeds %u-byte bound path=%s\n",
                    QUALIFICATION_INPUT_MAX_BYTES, path);
            fclose(file);
            return 0;
        }
        total += count;
        if (count != 0u) gbb_accept_sha256_update(&digest, buffer, count);
        if (count < sizeof(buffer)) {
            if (ferror(file)) {
                fprintf(stderr, "samesuite-apu suite: read failure for %s\n", path);
                fclose(file);
                return 0;
            }
            break;
        }
    }
    fclose(file);
    gbb_accept_sha256_final(&digest, actual);
    if (strcmp(actual, expected_sha256) == 0) return 1;
    fprintf(stderr,
            "samesuite-apu suite: qualification input digest mismatch path=%s expected=%s actual=%s\n",
            path, expected_sha256, actual);
    return 0;
}

static int verify_suite_identity(const char *manifest_path,
                                 const char *dispositions_path,
                                 const char *required_name) {
    size_t matches = 0u;
    if (GBB_SAMESUITE_APU_CASE_COUNT != 70u) {
        fprintf(stderr,
                "samesuite-apu suite: exact membership count mismatch expected=70 actual=%zu\n",
                GBB_SAMESUITE_APU_CASE_COUNT);
        return 0;
    }
    if (!file_matches_sha256(manifest_path, GBB_SAMESUITE_MANIFEST_SHA256) ||
        !file_matches_sha256(dispositions_path, GBB_SAMESUITE_DISPOSITIONS_SHA256))
        return 0;
    for (size_t i = 0u; i < GBB_SAMESUITE_APU_CASE_COUNT; ++i) {
        if (required_name == NULL || strcmp(samesuite_apu_cases[i].name, required_name) == 0)
            ++matches;
        for (size_t j = 0u; j < i; ++j) {
            if (strcmp(samesuite_apu_cases[i].name, samesuite_apu_cases[j].name) == 0) {
                fprintf(stderr, "samesuite-apu suite: duplicate identity=%s\n",
                        samesuite_apu_cases[i].name);
                return 0;
            }
        }
    }
    if (required_name != NULL && matches != 1u) {
        fprintf(stderr, "samesuite-apu suite: identity missing or duplicate=%s\n", required_name);
        return 0;
    }
    return 1;
}

static int run_suite(const char *manifest_path, const char *dispositions_path,
                     const char *fixture_root) {
    size_t pass_count = 0u;
    size_t xfail_count = 0u;
    size_t assertion_count = 0u;
    if (!verify_suite_identity(manifest_path, dispositions_path, NULL)) return 1;
    for (size_t i = 0u; i < GBB_SAMESUITE_APU_CASE_COUNT; ++i) {
        char path[1024u];
        const apu_case *test = &samesuite_apu_cases[i];
        const int written = snprintf(path, sizeof(path), "%s/%s", fixture_root,
                                     test->fixture_file);
        if (written < 0 || (size_t)written >= sizeof(path)) {
            fprintf(stderr, "samesuite-apu suite: fixture path too long case=%s\n", test->name);
            return 1;
        }
        if (run_case(test, path, 0, 0, test->expected_disposition,
                     test->expected_signature) != 0)
            return 1;
        assertion_count += test->result_count;
        if (strcmp(test->expected_disposition, "pass") == 0) ++pass_count;
        else if (strcmp(test->expected_disposition, "xfail") == 0) ++xfail_count;
        else {
            fprintf(stderr, "samesuite-apu suite: invalid disposition case=%s\n", test->name);
            return 1;
        }
    }
    fprintf(stderr,
            "samesuite-apu suite pass cases=%zu pass=%zu xfail=%zu assertions=%zu model=CGB-CPU-E mode=native speed=normal boot=bootless\n",
            GBB_SAMESUITE_APU_CASE_COUNT, pass_count, xfail_count, assertion_count);
    return pass_count == 8u && xfail_count == 62u && assertion_count == 4784u ? 0 : 1;
}

static int run_case(const apu_case *test, const char *rom_path,
                    int corrupt_direct_sample, int require_detected_mutation,
                    const char *expected_disposition,
                    const char *expected_signature) {
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
        if (run.reason == GBB_STOP_HALTED_IDLE) {
            terminal = 1;
            break;
        }
        if (run.consumed_half_dots == 0u || run.consumed_half_dots > slice) {
            fprintf(stderr,
                    "samesuite-apu run: invalid progress reason=%d consumed=%llu\n",
                    (int)run.reason, (unsigned long long)run.consumed_half_dots);
            gbb_destroy(machine);
            return 1;
        }
        elapsed += run.consumed_half_dots;
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
        observed[i] = gbb_peek_ram(machine, (uint16_t)(test->result_address + i));
    if (corrupt_direct_sample) observed[0] ^= 0x01u;
    const uint8_t result_code = gbb_peek_ram(machine, RESULT_CODE_ADDRESS);
    const int values_match = compare_results(test->expected_results, observed,
                                             test->result_count);
    const int guest_pass = values_match && result_code == (uint8_t)'P';
    char actual_signature[65];
    if (result_code != (uint8_t)'P' && result_code != (uint8_t)'F') {
        fprintf(stderr,
                "samesuite-apu guest-result case=%s invalid-terminal=%02x terminal=1 elapsed_half_dots=%llu run_calls=%u\n",
                test->name, result_code, (unsigned long long)elapsed, run_calls);
        gbb_destroy(machine);
        return 1;
    }
    if (!result_signature(test, result_code, observed, actual_signature)) {
        fprintf(stderr, "samesuite-apu signature: bounded encoding failed case=%s\n",
                test->name);
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
    if (expected_disposition != NULL && expected_signature != NULL) {
        if (strcmp(expected_disposition, "pass") == 0 && !guest_pass) {
            fprintf(stderr,
                    "samesuite-apu disposition: unexpected-failure case=%s expected=pass observed=fail signature=%s\n",
                    test->name, actual_signature);
            gbb_destroy(machine);
            return 1;
        }
        if (strcmp(expected_disposition, "xfail") == 0 && guest_pass) {
            fprintf(stderr,
                    "samesuite-apu disposition: unexpected-pass case=%s expected=xfail observed=pass signature=%s\n",
                    test->name, actual_signature);
            gbb_destroy(machine);
            return 1;
        }
        if (strcmp(expected_disposition, "pass") != 0 &&
            strcmp(expected_disposition, "xfail") != 0) {
            fprintf(stderr,
                    "samesuite-apu disposition: unknown-status case=%s value=%s\n",
                    test->name, expected_disposition);
            gbb_destroy(machine);
            return 1;
        }
        if (strcmp(actual_signature, expected_signature) != 0) {
            fprintf(stderr,
                    "samesuite-apu disposition: signature-changed case=%s expected=%s observed=%s\n",
                    test->name, expected_signature, actual_signature);
            gbb_destroy(machine);
            return 1;
        }
    }

    fprintf(stderr,
            "samesuite-apu guest-result case=%s author_expectation=P observed=%c evaluator_disposition=%s evaluator_status=%s terminal=1 elapsed_half_dots=%llu run_calls=%u assertions=%zu assertion_set=%s signature_sha256=%s test_sample_corruption=%s\n",
            test->name, (char)result_code,
            expected_disposition == NULL ? "not-qualified" :
                (strcmp(expected_disposition, "xfail") == 0
                    ? "expected-failure" : expected_disposition),
            expected_disposition != NULL ? expected_disposition : "unqualified",
            (unsigned long long)elapsed,
            run_calls, test->result_count,
            values_match ? "match" : "mismatch",
            actual_signature,
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
                                                rom_path, 1, 1, NULL, NULL);
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
        result = run_case(&CHANNEL_3_FIRST_SAMPLE, argv[2], 0, 0, NULL, NULL);
    else if (strcmp(name, "--controls") == 0 && argc == 3)
        result = tracer_controls(argv[2]);
    else if (strcmp(name, "--membership") == 0 && argc == 5)
        result = verify_suite_identity(argv[3], argv[4], argv[2]) ? 0 : 1;
    else if (strcmp(name, "--suite") == 0 && argc == 5)
        result = run_suite(argv[2], argv[3], argv[4]);
    else {
        fprintf(stderr, "samesuite-apu: invalid command\n");
        puts("not ok 1 - cgb_samesuite_apu command");
        return 2;
    }
    if (result == 0) {
        if (strcmp(name, "--tracer") == 0)
            puts("ok 1 - tracer recorded terminal guest observation");
        else if (strcmp(name, "--membership") == 0)
            puts("ok 1 - APU membership identity present");
        else if (strcmp(name, "--suite") == 0)
            puts("ok 1 - APU frozen qualification suite complete");
        else
            puts("ok 1 - cgb_samesuite_apu_tracer_controls");
        return 0;
    }
    if (strcmp(name, "--tracer") == 0)
        puts("not ok 1 - cgb_samesuite_apu_tracer");
    else if (strcmp(name, "--membership") == 0)
        puts("not ok 1 - APU membership identity");
    else if (strcmp(name, "--suite") == 0)
        puts("not ok 1 - APU frozen qualification suite");
    else
        puts("not ok 1 - cgb_samesuite_apu_tracer_controls");
    return result;
}
