#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Private core seams are intentionally declared here rather than added to the public ABI. */
extern void gbb_test_cpu_snapshot(const gbb_instance *instance, gbb_trace_record *record);

#ifdef GBB_AGE_P12
extern void gbb_p12_set_mutants(uint64_t mask);
extern int32_t gbb_p12_stall_offset_t;
#define AGE_STALL_OFFSET_MUTANT (UINT64_C(1) << 31)
#endif

#ifdef GBB_AGE_P14
extern void gbb_p14_set_mutants(uint64_t mask);
#define AGE_PHASE14_TRANSFER_MUTANT UINT64_C(1)
#endif

#define AGE_ROM_SIZE 0x8000u
#define AGE_TRACE_CAPACITY 1u
#define AGE_RUN_SLICE UINT64_C(2048)
#define AGE_MAX_ROWS 16u
#define AGE_PASS_B 3u
#define AGE_PASS_C 5u
#define AGE_PASS_D 8u
#define AGE_PASS_E 13u
#define AGE_PASS_H 21u
#define AGE_PASS_L 34u

typedef struct {
    const char *rom_path;
    uint16_t results_address;
    uint16_t expected_address;
    unsigned rows;
    uint64_t budget_half_dots;
} age_config;

typedef struct {
    int reached;
    int timed_out;
    int stopped;
    int register_pass;
    gbb_stop_reason stop_reason;
    uint64_t half_dots;
    unsigned rows_ok;
    uint16_t row_mask;
    uint8_t registers[6];
    uint8_t row_bytes[AGE_MAX_ROWS * 8u];
    char signature[65];
} age_result;

typedef enum {
    MODE_NONE = 0,
    MODE_VERDICT,
    MODE_PRINT_SIGNATURE,
    MODE_CHECK_DISPOSITION,
    MODE_STALL_WINDOW,
    MODE_SENSITIVITY,
    MODE_PHASE14_CONTROLS,
    MODE_SCAN
} age_mode;

static uint8_t age_rom[AGE_ROM_SIZE];
static uint64_t age_mutant_mask = 0u;
static int32_t age_stall_offset_t = 0;
static int age_has_stall_offset = 0;
static uint64_t age_phase14_mutant_mask = 0u;

static int parse_u64(const char *text, uint64_t *out) {
    char *end = NULL;
    unsigned long long value;
    if (text == NULL || text[0] == '\0' || text[0] == '-') return 0;
    errno = 0;
    value = strtoull(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0') return 0;
    *out = (uint64_t)value;
    return 1;
}

static int parse_signed(const char *text, int64_t *out) {
    char *end = NULL;
    long long value;
    if (text == NULL || text[0] == '\0') return 0;
    errno = 0;
    value = strtoll(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0') return 0;
    *out = (int64_t)value;
    return 1;
}

static int parse_hex_u16(const char *text, uint16_t *out) {
    char *end = NULL;
    unsigned long value;
    if (text == NULL || text[0] == '\0' || text[0] == '-') return 0;
    errno = 0;
    value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT16_MAX) return 0;
    *out = (uint16_t)value;
    return 1;
}

static int load_age_rom(const char *path) {
    FILE *file = fopen(path, "rb");
    size_t count;
    int extra;
    int failed;
    if (file == NULL) return 0;
    count = fread(age_rom, 1u, sizeof(age_rom), file);
    failed = ferror(file);
    extra = fgetc(file);
    fclose(file);
    return !failed && count == sizeof(age_rom) && extra == EOF;
}

static void configure_mutants(void) {
#ifdef GBB_AGE_P12
    gbb_p12_set_mutants(age_mutant_mask);
    if (age_has_stall_offset) gbb_p12_stall_offset_t = age_stall_offset_t;
#endif
#ifdef GBB_AGE_P14
    gbb_p14_set_mutants(age_phase14_mutant_mask);
#endif
}

static int row_address_valid(const age_config *config) {
    const uint32_t byte_count = config->rows * 8u;
    const uint32_t results_end = (uint32_t)config->results_address + byte_count;
    const uint32_t expected_end = (uint32_t)config->expected_address + 1u + byte_count;
    return config->rows > 0u && config->rows <= AGE_MAX_ROWS &&
           config->results_address >= 0xC000u && results_end <= 0xE000u &&
           expected_end <= AGE_ROM_SIZE;
}

static int read_verdict(const age_config *config, age_result *result) {
    static const uint8_t expected_registers[6] = {
        AGE_PASS_B, AGE_PASS_C, AGE_PASS_D, AGE_PASS_E, AGE_PASS_H, AGE_PASS_L
    };
    gbb_instance *instance = NULL;
    uint8_t digest_input[AGE_MAX_ROWS * 8u + 2u];
    gbb_error error;

    memset(result, 0, sizeof(*result));
    configure_mutants();
    error = gbb_create(GBB_PROFILE_CGB_CPU_E, &instance);
    if (error != GBB_OK || instance == NULL) {
        fprintf(stderr, "age-error create=%d\n", (int)error);
        gbb_destroy(instance);
        return 2;
    }
    error = gbb_load_rom(instance, age_rom, sizeof(age_rom));
    if (error != GBB_OK) {
        fprintf(stderr, "age-error load-rom=%d\n", (int)error);
        gbb_destroy(instance);
        return 2;
    }

    while (result->half_dots < config->budget_half_dots) {
        gbb_trace_record trace;
        const uint64_t remaining = config->budget_half_dots - result->half_dots;
        const uint64_t slice = remaining < AGE_RUN_SLICE ? remaining : AGE_RUN_SLICE;
        const gbb_run_result run = gbb_run(instance, slice, &trace, AGE_TRACE_CAPACITY);

        if (run.consumed_half_dots > remaining) {
            fprintf(stderr, "age-error core exceeded budget remaining=%" PRIu64 " consumed=%" PRIu64 "\n",
                    remaining, run.consumed_half_dots);
            gbb_destroy(instance);
            return 2;
        }
        result->half_dots += run.consumed_half_dots;
        if (run.trace_count > 1u) {
            fprintf(stderr, "age-error trace-count=%zu\n", run.trace_count);
            gbb_destroy(instance);
            return 2;
        }
        if (run.trace_count == 1u && trace.pc >= 0x0150u && trace.opcode[0] == 0x40u) {
            gbb_trace_record snapshot;
            gbb_test_cpu_snapshot(instance, &snapshot);
            result->reached = 1;
            result->registers[0] = snapshot.b;
            result->registers[1] = snapshot.c;
            result->registers[2] = snapshot.d;
            result->registers[3] = snapshot.e;
            result->registers[4] = snapshot.h;
            result->registers[5] = snapshot.l;
            result->register_pass = memcmp(result->registers, expected_registers,
                                           sizeof(expected_registers)) == 0;
            break;
        }
        if (run.reason == GBB_STOP_TRACE_FULL) {
            if (run.trace_count == 0u && run.consumed_half_dots == 0u) {
                fprintf(stderr, "age-error trace-full-without-progress\n");
                gbb_destroy(instance);
                return 2;
            }
            continue;
        }
        if (run.reason != GBB_STOP_BUDGET) {
            result->stopped = 1;
            result->stop_reason = run.reason;
            break;
        }
        if (run.consumed_half_dots == 0u) break;
    }
    if (!result->reached) {
        if (result->stopped) {
            fprintf(stderr, "age-error run-stopped reason=%d half_dots=%" PRIu64 "\n",
                    (int)result->stop_reason, result->half_dots);
            gbb_destroy(instance);
            return 2;
        }
        result->timed_out = 1;
        printf("age-timeout half_dots=%" PRIu64 "\n", result->half_dots);
        gbb_destroy(instance);
        return 3;
    }

    for (unsigned row = 0u; row < config->rows; ++row) {
        int row_matches = 1;
        for (unsigned byte = 0u; byte < 8u; ++byte) {
            const size_t index = row * 8u + byte;
            const uint8_t actual = gbb_peek_ram(instance,
                                                (uint16_t)(config->results_address + index));
            const uint8_t expected = age_rom[(size_t)config->expected_address + 1u + index];
            result->row_bytes[index] = actual;
            if (actual != expected) row_matches = 0;
        }
        if (row_matches) {
            result->row_mask = (uint16_t)(result->row_mask | (uint16_t)(1u << row));
            ++result->rows_ok;
        }
    }
    {
        const size_t result_bytes = (size_t)config->rows * 8u;
        digest_input[result_bytes] = (uint8_t)(result->row_mask & 0xFFu);
        digest_input[result_bytes + 1u] = (uint8_t)(result->row_mask >> 8);
        memcpy(digest_input, result->row_bytes, result_bytes);
        gbb_accept_sha256_hex(digest_input, result_bytes + 2u, result->signature);
    }
    gbb_destroy(instance);
    return 0;
}

static int valid_signature(const char *text, char out[65]) {
    size_t length;
    if (text == NULL) return 0;
    if (strncmp(text, "0x", 2u) == 0 || strncmp(text, "0X", 2u) == 0) text += 2;
    length = strlen(text);
    if (length != 64u) return 0;
    for (size_t i = 0u; i < length; ++i) {
        const char ch = text[i];
        if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f') ||
              (ch >= 'A' && ch <= 'F'))) return 0;
        out[i] = (ch >= 'A' && ch <= 'F') ? (char)(ch - 'A' + 'a') : ch;
    }
    out[64] = '\0';
    return 1;
}

static int parse_mask16(const char *text, uint16_t *out) {
    uint64_t value;
    if (text == NULL) return 0;
    if (strncmp(text, "0x", 2u) == 0 || strncmp(text, "0X", 2u) == 0) text += 2;
    if (text[0] == '\0') return 0;
    errno = 0;
    char *end = NULL;
    const unsigned long parsed = strtoul(text, &end, 16);
    if (errno != 0 || end == text || *end != '\0' || parsed > UINT16_MAX) return 0;
    value = (uint64_t)parsed;
    *out = (uint16_t)value;
    return 1;
}

static void print_result(const age_result *result, unsigned rows) {
    printf("age verdict=%s rows_ok=%u/%u mask=%04X signature=%s half_dots=%" PRIu64 "\n",
           result->register_pass ? "pass" : "fail", result->rows_ok, rows,
           (unsigned)result->row_mask, result->signature, result->half_dots);
}

static int run_and_print(const age_config *config, age_result *result) {
    const int code = read_verdict(config, result);
    if (code != 0) return code;
    print_result(result, config->rows);
    return 0;
}

static void print_row_hex(const uint8_t *bytes);

#ifdef GBB_AGE_P12
static const char *sensitivity_mutant_name(uint64_t mask) {
    if (mask == (UINT64_C(1) << 6)) return "M6";
    if (mask == (UINT64_C(1) << 21)) return "M21";
    if (mask == (UINT64_C(1) << 28)) return "M28";
    if (mask == (UINT64_C(1) << 27)) return "M27";
    return NULL;
}

static int sensitivity_expected_case(const char *json_path, uint64_t mask,
                                     const char *case_name, int *expected) {
    FILE *file = fopen(json_path, "rb");
    char marker[64];
    char *json = NULL;
    long file_size;
    const char *mutant;
    const char *cases;
    const char *array;
    const char *cursor;
    size_t case_length = strlen(case_name);
    int found = 0;

    if (file == NULL || sensitivity_mutant_name(mask) == NULL) {
        if (file != NULL) fclose(file);
        return 0;
    }
    if (fseek(file, 0, SEEK_END) != 0 || (file_size = ftell(file)) < 0 ||
        file_size > 1024 * 1024 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }
    json = (char *)malloc((size_t)file_size + 1u);
    if (json == NULL) {
        fclose(file);
        return 0;
    }
    if (fread(json, 1u, (size_t)file_size, file) != (size_t)file_size || ferror(file)) {
        free(json);
        fclose(file);
        return 0;
    }
    fclose(file);
    json[file_size] = '\0';
    (void)snprintf(marker, sizeof(marker), "\"mutant\": \"%s\"",
                   sensitivity_mutant_name(mask));
    mutant = strstr(json, marker);
    cases = mutant == NULL ? NULL : strstr(mutant, "\"discriminating_cases\"");
    array = cases == NULL ? NULL : strchr(cases, '[');
    if (array == NULL) {
        free(json);
        return 0;
    }
    cursor = array + 1;
    while (*cursor != '\0' && *cursor != ']') {
        if (*cursor != '"') {
            ++cursor;
            continue;
        }
        const char *start = ++cursor;
        while (*cursor != '\0' && *cursor != '"') {
            if (*cursor == '\\' && cursor[1] != '\0') ++cursor;
            ++cursor;
        }
        if (*cursor == '\0') break;
        if ((size_t)(cursor - start) == case_length &&
            memcmp(start, case_name, case_length) == 0) found = 1;
        ++cursor;
    }
    if (*cursor != ']') {
        free(json);
        return 0;
    }
    free(json);
    *expected = found;
    return 1;
}

static int age_case_name(const char *rom_path, char *out, size_t capacity) {
    const char *base = strrchr(rom_path, '/');
    const char *backslash = strrchr(rom_path, '\\');
    size_t length;
    if (backslash != NULL && (base == NULL || backslash > base)) base = backslash;
    base = base == NULL ? rom_path : base + 1;
    length = strlen(base);
    if (length >= 3u && strcmp(base + length - 3u, ".gb") == 0) length -= 3u;
    if (length == 0u || length >= capacity) return 0;
    memcpy(out, base, length);
    out[length] = '\0';
    return 1;
}

static int run_sensitivity(const age_config *config, uint64_t mutant_mask,
                           const char *json_path) {
    age_result clean;
    age_result mutant;
    char case_name[128];
    int expected_discriminates = 0;
    const char *mutant_name = sensitivity_mutant_name(mutant_mask);
    int code;

    if (mutant_name == NULL || !age_case_name(config->rom_path, case_name, sizeof(case_name)) ||
        !sensitivity_expected_case(json_path, mutant_mask, case_name, &expected_discriminates)) {
        fprintf(stderr, "age-error invalid sensitivity reference\n");
        return 2;
    }
    age_mutant_mask = 0u;
    code = read_verdict(config, &clean);
    if (code != 0) return code;
    age_mutant_mask = mutant_mask;
    code = read_verdict(config, &mutant);
    if (code != 0) return code;
    {
        const int discriminates = clean.register_pass != mutant.register_pass ||
            strcmp(clean.signature, mutant.signature) != 0;
        if (discriminates != expected_discriminates) {
            fprintf(stderr,
                "age-sensitivity mismatch mutant=%s case=%s expected=%s observed=%s clean=%s/%s mutant=%s/%s\n",
                mutant_name, case_name, expected_discriminates ? "discriminates" : "same",
                discriminates ? "discriminates" : "same",
                clean.register_pass ? "pass" : "fail", clean.signature,
                mutant.register_pass ? "pass" : "fail", mutant.signature);
            return 1;
        }
        printf("age-sensitivity pass mutant=%s case=%s discriminates=%s\n",
               mutant_name, case_name, discriminates ? "true" : "false");
    }
    return 0;
}
#endif

static const char *stat_mode_assertion_id(unsigned row) {
    static const char *const ids[14] = {
        "stat-mode-cgbE/mode-0/scx-0", "stat-mode-cgbE/mode-0/scx-1",
        "stat-mode-cgbE/mode-0/scx-2", "stat-mode-cgbE/mode-0/scx-3",
        "stat-mode-cgbE/mode-0/scx-4", "stat-mode-cgbE/mode-0/scx-5",
        "stat-mode-cgbE/mode-0/scx-6", "stat-mode-cgbE/mode-0/scx-7",
        "stat-mode-cgbE/mode-0/scx-8", "stat-mode-cgbE/mode-0/scx-9",
        "stat-mode-cgbE/mode-1-2/scx-0", "stat-mode-cgbE/mode-1-2/scx-7",
        "stat-mode-cgbE/mode-3/scx-0", "stat-mode-cgbE/mode-3/scx-7"
    };
    return row < sizeof(ids) / sizeof(ids[0]) ? ids[row] : NULL;
}

static void print_row_hex(const uint8_t *bytes) {
    for (unsigned byte = 0u; byte < 8u; ++byte) printf("%02X", bytes[byte]);
}

static int run_phase14_controls(const age_config *config,
                                const char *expected_signature,
                                uint16_t expected_mask) {
#ifdef GBB_AGE_P14
    age_result clean;
    age_result mutant;
    const char *base = strrchr(config->rom_path, '/');
    const char *case_name;
    int code;

    base = base == NULL ? config->rom_path : base + 1;
    if (strcmp(base, "stat-mode-cgbE.gb") != 0 || config->rows != 14u) {
        fprintf(stderr, "age-phase14-control unexpected-tracer-case\n");
        return 2;
    }
    case_name = "stat-mode-cgbE";
    age_phase14_mutant_mask = 0u;
    code = read_verdict(config, &clean);
    if (code != 0) return code;
    if (clean.register_pass || clean.row_mask != expected_mask ||
        strcmp(clean.signature, expected_signature) != 0) {
        fprintf(stderr,
                "age-phase14-control baseline-drift expected=%s/%04X observed=%s/%04X\n",
                expected_signature, (unsigned)expected_mask, clean.signature,
                (unsigned)clean.row_mask);
        return 1;
    }

    printf("age-phase14-control baseline=matched-xfail case=%s rows=%u/%u mask=%04X signature=%s\n",
           case_name, clean.rows_ok, config->rows, (unsigned)clean.row_mask,
           clean.signature);
    for (unsigned row = 0u; row < config->rows; ++row) {
        const size_t offset = (size_t)row * 8u;
        const uint8_t *expected = age_rom + (size_t)config->expected_address + 1u + offset;
        printf("age-assertion id=%s row=%u expected=", stat_mode_assertion_id(row), row);
        print_row_hex(expected);
        printf(" actual=");
        print_row_hex(clean.row_bytes + offset);
        printf(" disposition=%s\n",
               (clean.row_mask & (uint16_t)(1u << row)) != 0u ? "pass" : "fail");
    }

    age_phase14_mutant_mask = AGE_PHASE14_TRANSFER_MUTANT;
    code = read_verdict(config, &mutant);
    if (code != 0) return code;
    if (mutant.register_pass ||
        (mutant.row_mask == clean.row_mask &&
         strcmp(mutant.signature, clean.signature) == 0)) {
        fprintf(stderr, "age-phase14-control intended-mutation-not-detected case=%s\n",
                case_name);
        return 1;
    }
    for (unsigned row = 0u; row < config->rows; ++row) {
        const size_t offset = (size_t)row * 8u;
        const uint8_t *expected = age_rom + (size_t)config->expected_address + 1u + offset;
        if (memcmp(clean.row_bytes + offset, mutant.row_bytes + offset, 8u) != 0 &&
            memcmp(expected, mutant.row_bytes + offset, 8u) != 0) {
            printf("age-phase14-control intended-mismatch assertion=%s row=%u expected=",
                   stat_mode_assertion_id(row), row);
            print_row_hex(expected);
            printf(" baseline=");
            print_row_hex(clean.row_bytes + offset);
            printf(" mutant=");
            print_row_hex(mutant.row_bytes + offset);
            printf(" signature=%s mask=%04X\n", mutant.signature,
                   (unsigned)mutant.row_mask);
            return 0;
        }
    }
    fprintf(stderr, "age-phase14-control mutation-did-not-break-named-row case=%s\n",
            case_name);
    return 1;
#else
    (void)config;
    (void)expected_signature;
    (void)expected_mask;
    fprintf(stderr, "age-phase14-control requires the private Phase 14 mutant build\n");
    return 2;
#endif
}

static int set_mode(age_mode *mode, age_mode next) {
    if (*mode != MODE_NONE) return 0;
    *mode = next;
    return 1;
}

int main(int argc, char **argv) {
    age_config config;
    age_mode mode = MODE_NONE;
    const char *disposition = NULL;
    char expected_signature[65] = {0};
    uint16_t expected_mask = 0u;
    int have_expected_signature = 0;
    int print_phase14_observations = 0;
    uint64_t parsed = 0u;
    const char *sensitivity_json_path = NULL;
    int64_t window_constant = 0;
    int64_t window_lo = 0;
    int64_t window_hi = 0;
    int64_t scan_from = 0;
    int64_t scan_to = 0;

    if (argc < 7 || !parse_hex_u16(argv[2], &config.results_address) ||
        !parse_hex_u16(argv[3], &config.expected_address) ||
        !parse_u64(argv[4], &parsed) || parsed == 0u || parsed > AGE_MAX_ROWS) {
        fprintf(stderr, "usage: test_age <rom> <results-hex> <expected-hex> <rows> <budget-half-dots> <mode> [mode args]\n");
        return 2;
    }
    config.rom_path = argv[1];
    config.rows = (unsigned)parsed;
    if (!parse_u64(argv[5], &config.budget_half_dots) || config.budget_half_dots == 0u ||
        !row_address_valid(&config)) {
        fprintf(stderr, "age-error invalid manifest bounds or budget\n");
        return 2;
    }
    if (!load_age_rom(config.rom_path)) {
        fprintf(stderr, "age-error fixture must be exactly %u bytes: %s\n", AGE_ROM_SIZE, config.rom_path);
        return 2;
    }

    for (int i = 6; i < argc; ++i) {
        if (strcmp(argv[i], "--verdict") == 0) {
            if (!set_mode(&mode, MODE_VERDICT)) goto bad_mode;
        } else if (strcmp(argv[i], "--print-signature") == 0) {
            if (!set_mode(&mode, MODE_PRINT_SIGNATURE)) goto bad_mode;
        } else if (strcmp(argv[i], "--check-disposition") == 0) {
            if (!set_mode(&mode, MODE_CHECK_DISPOSITION) || i + 1 >= argc) goto bad_mode;
            disposition = argv[++i];
            if (strcmp(disposition, "pass") != 0 && strcmp(disposition, "expected-failure") != 0) goto bad_mode;
            if (strcmp(disposition, "expected-failure") == 0) {
                if (i + 2 >= argc || !valid_signature(argv[i + 1], expected_signature) ||
                    !parse_mask16(argv[i + 2], &expected_mask)) goto bad_mode;
                i += 2;
                have_expected_signature = 1;
            }
        } else if (strcmp(argv[i], "--mutants") == 0) {
#ifdef GBB_AGE_P12
            if (i + 1 >= argc || !parse_u64(argv[++i], &age_mutant_mask)) goto bad_mode;
#else
            goto bad_mode;
#endif
        } else if (strcmp(argv[i], "--stall-offset-t") == 0) {
#ifdef GBB_AGE_P12
            int64_t offset;
            if (i + 1 >= argc || !parse_signed(argv[++i], &offset) ||
                offset < INT32_MIN || offset > INT32_MAX) goto bad_mode;
            age_stall_offset_t = (int32_t)offset;
            age_mutant_mask |= AGE_STALL_OFFSET_MUTANT;
            age_has_stall_offset = 1;
#else
            goto bad_mode;
#endif
        } else if (strcmp(argv[i], "--stall-window") == 0) {
#ifdef GBB_AGE_P12
            if (!set_mode(&mode, MODE_STALL_WINDOW) || i + 3 >= argc ||
                !parse_signed(argv[++i], &window_constant) ||
                !parse_signed(argv[++i], &window_lo) || !parse_signed(argv[++i], &window_hi) ||
                window_constant < 0 || window_lo < 0 || window_hi < window_lo) goto bad_mode;
#else
            goto bad_mode;
#endif
        } else if (strcmp(argv[i], "--sensitivity") == 0) {
#ifdef GBB_AGE_P12
            if (!set_mode(&mode, MODE_SENSITIVITY) || i + 2 >= argc ||
                !parse_u64(argv[++i], &age_mutant_mask)) goto bad_mode;
            sensitivity_json_path = argv[++i];
#else
            goto bad_mode;
#endif
        } else if (strcmp(argv[i], "--phase14-controls") == 0) {
            if (!set_mode(&mode, MODE_PHASE14_CONTROLS) || i + 2 >= argc ||
                !valid_signature(argv[++i], expected_signature) ||
                !parse_mask16(argv[++i], &expected_mask)) goto bad_mode;
            have_expected_signature = 1;
        } else if (strcmp(argv[i], "--phase14-observations") == 0) {
            if (print_phase14_observations) goto bad_mode;
            print_phase14_observations = 1;
        } else if (strcmp(argv[i], "--scan") == 0) {
#ifdef GBB_AGE_P12
            if (!set_mode(&mode, MODE_SCAN) || i + 2 >= argc ||
                !parse_signed(argv[++i], &scan_from) || !parse_signed(argv[++i], &scan_to) ||
                scan_from > scan_to || scan_to - scan_from > 256) goto bad_mode;
#else
            goto bad_mode;
#endif
        } else {
            goto bad_mode;
        }
    }
    if (mode == MODE_NONE) goto bad_mode;
    if (print_phase14_observations && mode != MODE_CHECK_DISPOSITION) goto bad_mode;

    if (mode == MODE_STALL_WINDOW) {
#ifdef GBB_AGE_P12
        const int64_t offsets[4] = {
            window_lo - 1 - window_constant,
            window_lo - window_constant,
            window_hi - window_constant,
            window_hi + 1 - window_constant
        };
        const int expected_pass[4] = {0, 1, 1, 0};
        int observed_pass[4] = {0, 0, 0, 0};
        age_mutant_mask |= AGE_STALL_OFFSET_MUTANT;
        for (unsigned i = 0u; i < 4u; ++i) {
            age_result result;
            int code;
            if (offsets[i] < INT32_MIN || offsets[i] > INT32_MAX) goto bad_mode;
            age_stall_offset_t = (int32_t)offsets[i];
            age_has_stall_offset = 1;
            code = run_and_print(&config, &result);
            if (code != 0) return code;
            observed_pass[i] = result.register_pass;
        }
        if (memcmp(observed_pass, expected_pass, sizeof(expected_pass)) != 0) {
            printf("age-stall-window moved verdicts=<%s,%s,%s,%s>\n",
                   observed_pass[0] ? "pass" : "fail", observed_pass[1] ? "pass" : "fail",
                   observed_pass[2] ? "pass" : "fail", observed_pass[3] ? "pass" : "fail");
            return 1;
        }
        printf("age-stall-window pass window=[0x%" PRIx64 ",0x%" PRIx64 "] constant=0x%" PRIx64 "\n",
               (uint64_t)window_lo, (uint64_t)window_hi, (uint64_t)window_constant);
        return 0;
#endif
    }

    if (mode == MODE_SCAN) {
#ifdef GBB_AGE_P12
        age_mutant_mask |= AGE_STALL_OFFSET_MUTANT;
        for (int64_t offset = scan_from; offset <= scan_to; ++offset) {
            age_result result;
            int code;
            if (offset < INT32_MIN || offset > INT32_MAX) goto bad_mode;
            age_stall_offset_t = (int32_t)offset;
            age_has_stall_offset = 1;
            code = read_verdict(&config, &result);
            if (code != 0) return code;
            printf("offset=%" PRId64 " verdict=%s rows_ok=%u/%u\n", offset,
                   result.register_pass ? "pass" : "fail", result.rows_ok, config.rows);
        }
        return 0;
#endif
    }

    if (mode == MODE_SENSITIVITY) {
#ifdef GBB_AGE_P12
        if (sensitivity_json_path == NULL) goto bad_mode;
        return run_sensitivity(&config, age_mutant_mask, sensitivity_json_path);
#else
        goto bad_mode;
#endif
    }

    if (mode == MODE_PHASE14_CONTROLS) {
        if (!have_expected_signature) goto bad_mode;
        return run_phase14_controls(&config, expected_signature, expected_mask);
    }

    {
        age_result result;
        const int code = run_and_print(&config, &result);
        if (code != 0) return code;
        if (print_phase14_observations) {
            const char *base = strrchr(config.rom_path, '/');
            char case_name[128];
            size_t length;
            base = base == NULL ? config.rom_path : base + 1;
            length = strlen(base);
            if (length > 3u && strcmp(base + length - 3u, ".gb") == 0) length -= 3u;
            if (length == 0u || length >= sizeof(case_name)) goto bad_mode;
            memcpy(case_name, base, length);
            case_name[length] = '\0';
            for (unsigned row = 0u; row < config.rows; ++row) {
                const size_t offset = (size_t)row * 8u;
                const uint8_t *expected = age_rom + (size_t)config.expected_address + 1u + offset;
                const uint8_t *actual = result.row_bytes + offset;
                if (strcmp(case_name, "stat-mode-cgbE") == 0) {
                    const char *assertion_id = stat_mode_assertion_id(row);
                    if (assertion_id == NULL) goto bad_mode;
                    printf("age-assertion-row id=%s expected=", assertion_id);
                } else {
                    printf("age-assertion-row id=%s/row-%02u expected=", case_name, row);
                }
                print_row_hex(expected);
                printf(" actual=");
                print_row_hex(actual);
                printf(" disposition=%s\n",
                       (result.row_mask & (uint16_t)(1u << row)) != 0u ? "pass" : "fail");
            }
        }
        if (mode == MODE_CHECK_DISPOSITION) {
            if (strcmp(disposition, "pass") == 0) {
                if (!result.register_pass || result.rows_ok != config.rows) {
                    fprintf(stderr, "age-disposition-mismatch expected=pass\n");
                    return 1;
                }
                return 0;
            }
            if (!have_expected_signature) return 2;
            if (result.register_pass) {
                fprintf(stderr, "age-expected-failure-now-passes\n");
                return 1;
            }
            if (strcmp(result.signature, expected_signature) != 0 || result.row_mask != expected_mask) {
                fprintf(stderr, "age-signature-changed expected=%s/%04X observed=%s/%04X\n",
                        expected_signature, (unsigned)expected_mask, result.signature,
                        (unsigned)result.row_mask);
                return 1;
            }
        }
        return 0;
    }

bad_mode:
    fprintf(stderr, "age-error invalid mode or arguments\n");
    return 2;
}
