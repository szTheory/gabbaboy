#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef GBB_P12_PUBLIC_MUTANT
extern void gbb_p12_set_mutants(uint64_t mask);
#endif

#define FRAME_HALF_DOTS UINT64_C(140448)
#define MAX_EXPECTATIONS 128u
#define SAMPLE_BASE 0xC100u
#define SAMPLE_STRIDE 32u
#define DONE_ADDRESS 0xC0FEu
#define HOSTILE_MARKER_ADDRESS 0xC1F0u
#define HOSTILE_OUTCOME_BASE 0xC200u
#define HOSTILE_SELECTOR_OFFSET 0x0200u
#define DIGEST_FRAMES 60u
#define PCM_CAPACITY 1024u
#define REQUIRE(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "cgb-speed-fixture assertion failed: %s:%d: %s\n", \
                __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

#define AUDIO_DIGEST_PIN "126c6ddf5cf8f0e2fb394e8978c1ad018b633e0bd8e1a0785ecb6cca72d4db82"
#define FRAME_DIGEST_PIN "1f550c49fa9c6c3e99fbb3cc2982198125a89eb0c2ef6ca95e3c935bcbb7a100"

static const char *const METRICS[] = {
    "tima", "div", "serial-lines", "serial-sc", "serial-if", "nr52-start",
    "nr52-lines", "nr52-end", "dma-159", "dma-161", "key1", "key1-armed",
    "stop-lines", "key1-after"
};

static const char *const HOSTILE_METRICS[] = {
    "hostile-key1-before", "hostile-key1-armed", "hostile-key1-after",
    "hostile-double-speed", "hostile-handler", "hostile-lines",
    "hostile-halt", "hostile-if", "hostile-div", "hostile-dma"
};

typedef struct {
    char name[24];
    unsigned phase;
    unsigned low;
    unsigned high;
} expectation;

static int load_rom(const char *path, uint8_t **bytes, size_t *size) {
    FILE *file = fopen(path, "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) {
        if (file != NULL) fclose(file);
        return 1;
    }
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 1;
    }
    uint8_t *data = malloc((size_t)length);
    if (data == NULL || fread(data, 1u, (size_t)length, file) != (size_t)length) {
        free(data);
        fclose(file);
        return 1;
    }
    fclose(file);
    *bytes = data;
    *size = (size_t)length;
    return 0;
}

static int run_to_done(gbb_instance *machine, int *saw_halted_idle) {
    for (unsigned frame = 0; frame < 60u; ++frame) {
        gbb_run_result result = gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u);
        if (saw_halted_idle != NULL && result.reason == GBB_STOP_HALTED_IDLE &&
            gbb_peek_ram(machine, DONE_ADDRESS) != 1u)
            *saw_halted_idle = 1;
        if (result.reason != GBB_STOP_BUDGET &&
            result.reason != GBB_STOP_HALTED_IDLE &&
            result.reason != GBB_STOP_NO_PROGRESS) {
            fprintf(stderr, "cgb-speed-fixture run-fail reason=%d frame=%u\n",
                    (int)result.reason, frame);
            return 1;
        }
        if (gbb_peek_ram(machine, DONE_ADDRESS) == 1u) return 0;
    }
    fprintf(stderr, "cgb-speed-fixture timeout frames=120\n");
    return 1;
}

static int read_expectations(const char *path, expectation rows[MAX_EXPECTATIONS], size_t *count) {
    FILE *file = fopen(path, "r");
    if (file == NULL) return 1;
    *count = 0u;
    unsigned seen[sizeof(METRICS) / sizeof(METRICS[0])][4] = {{0u}};
    for (;;) {
        expectation row;
        int read = fscanf(file, "%23s %u %u %u", row.name, &row.phase, &row.low, &row.high);
        if (read == EOF) break;
        if (read != 4 || row.low > row.high) {
            fclose(file);
            return 1;
        }
        if (strncmp(row.name, "hostile-", 8u) == 0) continue;
        if (*count == MAX_EXPECTATIONS || row.phase > 3u) {
            fclose(file);
            return 1;
        }
        size_t metric = 0u;
        while (metric < sizeof(METRICS) / sizeof(METRICS[0]) &&
               strcmp(row.name, METRICS[metric]) != 0) ++metric;
        if (metric == sizeof(METRICS) / sizeof(METRICS[0]) || seen[metric][row.phase] != 0u ||
            ((metric >= 11u) && row.phase == 3u)) {
            fclose(file);
            return 1;
        }
        seen[metric][row.phase] = 1u;
        rows[(*count)++] = row;
    }
    fclose(file);
    if (*count != 53u) return 1;
    for (size_t metric = 0u; metric < sizeof(METRICS) / sizeof(METRICS[0]); ++metric) {
        const unsigned phases = metric >= 11u ? 3u : 4u;
        for (unsigned phase = 0u; phase < phases; ++phase)
            if (seen[metric][phase] != 1u) return 1;
    }
    return 0;
}

static unsigned sample(const gbb_instance *machine, unsigned phase, unsigned offset) {
    return gbb_peek_ram(machine, (uint16_t)(SAMPLE_BASE + phase * SAMPLE_STRIDE + offset));
}

static int actual_value(const gbb_instance *machine, const expectation *row, unsigned *value) {
    unsigned base = row->phase * SAMPLE_STRIDE;
    if (strcmp(row->name, "tima") == 0) {
        *value = sample(machine, row->phase, 3u);
    } else if (strcmp(row->name, "div") == 0) {
        *value = sample(machine, row->phase, 4u);
    } else if (strcmp(row->name, "serial-lines") == 0) {
        *value = sample(machine, row->phase, 5u);
    } else if (strcmp(row->name, "serial-sc") == 0) {
        *value = sample(machine, row->phase, 6u);
    } else if (strcmp(row->name, "serial-if") == 0) {
        *value = sample(machine, row->phase, 7u);
    } else if (strcmp(row->name, "nr52-start") == 0) {
        *value = sample(machine, row->phase, 8u);
    } else if (strcmp(row->name, "nr52-lines") == 0) {
        *value = sample(machine, row->phase, 9u);
    } else if (strcmp(row->name, "nr52-end") == 0) {
        *value = sample(machine, row->phase, 10u);
    } else if (strcmp(row->name, "dma-159") == 0) {
        *value = sample(machine, row->phase, 11u);
    } else if (strcmp(row->name, "dma-161") == 0) {
        *value = sample(machine, row->phase, 12u);
    } else if (strcmp(row->name, "key1") == 0) {
        *value = sample(machine, row->phase, 0u);
    } else if (strcmp(row->name, "key1-armed") == 0) {
        *value = sample(machine, row->phase, 1u);
    } else if (strcmp(row->name, "key1-after") == 0) {
        *value = sample(machine, row->phase, 2u);
    } else if (strcmp(row->name, "stop-lines") == 0 && row->phase < 3u) {
        unsigned before = gbb_peek_ram(machine, (uint16_t)(SAMPLE_BASE + base + 13u));
        unsigned after = gbb_peek_ram(machine, (uint16_t)(SAMPLE_BASE + base + 15u));
        *value = (after + 154u - before) % 154u;
    } else {
        return 1;
    }
    return 0;
}

static int probes(const char *rom_path, const char *table_path) {
    uint8_t *rom = NULL;
    size_t rom_size = 0u;
    REQUIRE(load_rom(rom_path, &rom, &rom_size) == 0);
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    free(rom);
    REQUIRE(run_to_done(machine, NULL) == 0);

    expectation rows[MAX_EXPECTATIONS];
    size_t count = 0u;
    REQUIRE(read_expectations(table_path, rows, &count) == 0);
    unsigned checks = 0u;
    for (size_t i = 0; i < count; ++i) {
        unsigned value = 0u;
        if (actual_value(machine, &rows[i], &value) != 0) {
            fprintf(stderr, "cgb-speed-fixture expectation-invalid %s phase=%u\n",
                    rows[i].name, rows[i].phase);
            gbb_destroy(machine);
            return 1;
        }
        if (value < rows[i].low || value > rows[i].high) {
            fprintf(stderr, "cgb-speed-fixture verdict-fail %s %u got=%u want=[%u,%u]\n",
                    rows[i].name, rows[i].phase, value, rows[i].low, rows[i].high);
            gbb_destroy(machine);
            return 1;
        }
        ++checks;
    }
    gbb_destroy(machine);
    printf("cgb-speed-fixture probes pass checks=%u\n", checks);
    return 0;
}

static int hostile_metric_index(const char *name) {
    for (size_t i = 0u; i < sizeof(HOSTILE_METRICS) / sizeof(HOSTILE_METRICS[0]); ++i)
        if (strcmp(name, HOSTILE_METRICS[i]) == 0) return (int)i;
    return -1;
}

static int read_hostile_expectations(const char *path, expectation rows[MAX_EXPECTATIONS],
                                    size_t *count, unsigned *max_entry) {
    FILE *file = fopen(path, "r");
    if (file == NULL) return 1;
    unsigned seen[sizeof(HOSTILE_METRICS) / sizeof(HOSTILE_METRICS[0])][9] = {{0u}};
    *count = 0u;
    *max_entry = 0u;
    for (;;) {
        expectation row;
        int read = fscanf(file, "%23s %u %u %u", row.name, &row.phase, &row.low, &row.high);
        if (read == EOF) break;
        if (read != 4 || row.low > row.high) {
            fclose(file);
            return 1;
        }
        if (strncmp(row.name, "hostile-", 8u) != 0) continue;
        const int metric = hostile_metric_index(row.name);
        if (metric < 0 || row.phase == 0u || row.phase > 8u || *count == MAX_EXPECTATIONS ||
            seen[(size_t)metric][row.phase] != 0u) {
            fclose(file);
            return 1;
        }
        seen[(size_t)metric][row.phase] = 1u;
        rows[(*count)++] = row;
        if (row.phase > *max_entry) *max_entry = row.phase;
    }
    fclose(file);
    if (*max_entry == 0u) return 1;
    for (unsigned entry = 1u; entry <= *max_entry; ++entry)
        for (size_t metric = 0u; metric < 8u; ++metric)
            if (seen[metric][entry] == 0u) return 1;
    if (*max_entry >= 6u && seen[8][6] != 1u) return 1;
    if (*max_entry >= 7u && seen[9][7] != 1u) return 1;
    return 0;
}

static unsigned hostile_byte(const gbb_instance *machine, unsigned offset) {
    return gbb_peek_ram(machine, (uint16_t)(HOSTILE_OUTCOME_BASE + offset));
}

static int hostile_actual(const gbb_instance *machine, const expectation *row,
                          int saw_halted_idle, unsigned *value) {
    if (strcmp(row->name, "hostile-key1-before") == 0) {
        *value = hostile_byte(machine, 2u);
    } else if (strcmp(row->name, "hostile-key1-armed") == 0) {
        *value = hostile_byte(machine, 3u);
    } else if (strcmp(row->name, "hostile-key1-after") == 0) {
        *value = hostile_byte(machine, 4u);
    } else if (strcmp(row->name, "hostile-double-speed") == 0) {
        *value = (hostile_byte(machine, 4u) >> 7) & 1u;
    } else if (strcmp(row->name, "hostile-handler") == 0) {
        *value = hostile_byte(machine, 5u);
    } else if (strcmp(row->name, "hostile-lines") == 0) {
        const unsigned before = hostile_byte(machine, 6u);
        const unsigned after = hostile_byte(machine, 7u);
        *value = (after + 154u - before) % 154u;
    } else if (strcmp(row->name, "hostile-halt") == 0) {
        *value = saw_halted_idle != 0 ? 1u : 0u;
    } else if (strcmp(row->name, "hostile-if") == 0) {
        *value = hostile_byte(machine, 8u);
    } else if (strcmp(row->name, "hostile-div") == 0) {
        *value = hostile_byte(machine, 10u);
    } else if (strcmp(row->name, "hostile-dma") == 0) {
        *value = hostile_byte(machine, 11u);
    } else {
        return 1;
    }
    return 0;
}

static int run_hostile_selector(const uint8_t *original, size_t rom_size, unsigned selector,
                                const expectation *rows, size_t row_count,
                                int *saw_halted_idle) {
    uint8_t *patched = malloc(rom_size);
    if (patched == NULL) return 1;
    memcpy(patched, original, rom_size);
    patched[HOSTILE_SELECTOR_OFFSET] = (uint8_t)selector;

    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK || machine == NULL) {
        free(patched);
        return 1;
    }
    if (gbb_load_rom(machine, patched, rom_size) != GBB_OK) {
        gbb_destroy(machine);
        free(patched);
        fprintf(stderr, "cgb-speed-fixture hostile-load-fail selector=%u\n", selector);
        return 1;
    }
    free(patched);
    if (selector == 4u) {
        const gbb_input_event press = {0u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT};
        if (gbb_queue_events(machine, &press, 1u) != GBB_OK) {
            gbb_destroy(machine);
            return 1;
        }
    }
    if (run_to_done(machine, saw_halted_idle) != 0) {
        gbb_destroy(machine);
        return 1;
    }
    const unsigned marker = gbb_peek_ram(machine, HOSTILE_MARKER_ADDRESS);
    const unsigned expected_marker = selector == 0u ? 0xA0u : selector == 9u ? 0xA9u : 1u;
    if (marker != expected_marker) {
        fprintf(stderr, "cgb-speed-fixture verdict-fail hostile-%u marker got=%u want=%u\n",
                selector, marker, expected_marker);
        gbb_destroy(machine);
        return 1;
    }
    if (selector != 0u && selector != 9u) {
        if (hostile_byte(machine, 1u) != selector) {
            fprintf(stderr, "cgb-speed-fixture verdict-fail hostile-%u selector got=%u want=%u\n",
                    selector, hostile_byte(machine, 1u), selector);
            gbb_destroy(machine);
            return 1;
        }
        for (size_t i = 0u; i < row_count; ++i) {
            if (rows[i].phase != selector) continue;
            unsigned value = 0u;
            if (hostile_actual(machine, &rows[i], *saw_halted_idle, &value) != 0) {
                gbb_destroy(machine);
                return 1;
            }
            if (value < rows[i].low || value > rows[i].high) {
                fprintf(stderr, "cgb-speed-fixture verdict-fail hostile-%u %s got=%u want=[%u,%u]\n",
                        selector, rows[i].name, value, rows[i].low, rows[i].high);
                gbb_destroy(machine);
                return 1;
            }
        }
    }
    gbb_destroy(machine);
    return 0;
}

static int hostile(const char *rom_path, const char *table_path) {
    uint8_t *original = NULL;
    size_t rom_size = 0u;
    if (load_rom(rom_path, &original, &rom_size) != 0 ||
        rom_size <= HOSTILE_SELECTOR_OFFSET || original[HOSTILE_SELECTOR_OFFSET] != 0u) {
        free(original);
        fprintf(stderr, "cgb-speed-fixture hostile-base-invalid\n");
        return 1;
    }
    expectation rows[MAX_EXPECTATIONS];
    size_t row_count = 0u;
    unsigned max_entry = 0u;
    if (read_hostile_expectations(table_path, rows, &row_count, &max_entry) != 0) {
        free(original);
        fprintf(stderr, "cgb-speed-fixture hostile-expectations-invalid\n");
        return 1;
    }
    int saw_halted_idle = 0;
    if (run_hostile_selector(original, rom_size, 0u, rows, row_count, &saw_halted_idle) != 0) {
        free(original);
        return 1;
    }
    for (unsigned selector = 1u; selector <= max_entry; ++selector) {
        saw_halted_idle = 0;
        if (run_hostile_selector(original, rom_size, selector, rows, row_count,
                                 &saw_halted_idle) != 0) {
            free(original);
            return 1;
        }
    }
    saw_halted_idle = 0;
    if (run_hostile_selector(original, rom_size, 9u, rows, row_count, &saw_halted_idle) != 0) {
        free(original);
        return 1;
    }
    if (original[HOSTILE_SELECTOR_OFFSET] != 0u) {
        free(original);
        fprintf(stderr, "cgb-speed-fixture hostile-base-mutated\n");
        return 1;
    }
    free(original);
    printf("cgb-speed-fixture hostile pass entries=%u\n", max_entry + 2u);
    return 0;
}

static int run_digest_frames(gbb_instance *machine, gbb_accept_pcm_digest_ctx *pcm_digest,
                             uint16_t *last_frame) {
    gbb_audio_frame audio[PCM_CAPACITY];
    uint64_t pending_half_dots = 0u;
    for (unsigned frame = 0u; frame < DIGEST_FRAMES; ++frame) {
        pending_half_dots += FRAME_HALF_DOTS;
        while (pending_half_dots != 0u) {
            size_t count = 0u;
            const gbb_run_result result = gbb_run_audio(machine, pending_half_dots,
                audio, PCM_CAPACITY, &count);
            if (result.consumed_half_dots > pending_half_dots) {
                fprintf(stderr, "cgb-speed-fixture digest-run over-consumed frame=%u\n", frame);
                return 1;
            }
            if (pcm_digest != NULL) gbb_accept_pcm_digest_feed(pcm_digest, audio, count);
            pending_half_dots -= result.consumed_half_dots;
            if (pending_half_dots == 0u) break;
            if (result.reason == GBB_STOP_OUTPUT_FULL && result.consumed_half_dots != 0u) continue;
            if (result.reason == GBB_STOP_BUDGET || result.reason == GBB_STOP_HALTED_IDLE ||
                result.reason == GBB_STOP_NO_PROGRESS) break;
            fprintf(stderr, "cgb-speed-fixture digest-run reason=%d frame=%u\n",
                    (int)result.reason, frame);
            return 1;
        }
    }
    if (last_frame != NULL) {
        gbb_frame_info info;
        const gbb_error result = gbb_copy_frame_rgb555(machine, last_frame,
            sizeof(uint16_t) * GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT,
            GBB_ACCEPT_FRAME_WIDTH * sizeof(uint16_t), &info);
        if (result != GBB_OK) {
            fprintf(stderr, "cgb-speed-fixture frame-copy error=%d\n", (int)result);
            return 1;
        }
    }
    return 0;
}

static int digest_case(const char *kind, const char *rom_path) {
    uint8_t *rom = NULL;
    size_t rom_size = 0u;
    REQUIRE(load_rom(rom_path, &rom, &rom_size) == 0);
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    free(rom);

    char observed[65];
    if (strcmp(kind, "audio") == 0) {
        gbb_accept_pcm_digest_ctx digest;
        gbb_accept_pcm_digest_init(&digest);
        REQUIRE(run_digest_frames(machine, &digest, NULL) == 0);
        gbb_accept_pcm_digest_final(&digest, observed);
        if (strcmp(observed, AUDIO_DIGEST_PIN) != 0) {
            fprintf(stderr, "cgb-speed-fixture audio-digest mismatch observed audio %s expected=%s\n",
                    observed, AUDIO_DIGEST_PIN);
            gbb_destroy(machine);
            return 1;
        }
        printf("cgb-speed-fixture audio-digest pass frames=%u sha256=%s\n",
                DIGEST_FRAMES, observed);
    } else if (strcmp(kind, "frame") == 0) {
        uint16_t pixels[GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT];
        REQUIRE(run_digest_frames(machine, NULL, pixels) == 0);
        if (gbb_accept_rgb555_digest(pixels,
                GBB_ACCEPT_FRAME_WIDTH * sizeof(uint16_t), observed) != 0) {
            gbb_destroy(machine);
            return 1;
        }
        if (strcmp(observed, FRAME_DIGEST_PIN) != 0) {
            fprintf(stderr, "cgb-speed-fixture frame-digest mismatch observed frame %s expected=%s\n",
                    observed, FRAME_DIGEST_PIN);
            gbb_destroy(machine);
            return 1;
        }
        printf("cgb-speed-fixture frame-digest pass frames=%u sha256=%s\n",
                DIGEST_FRAMES, observed);
    } else {
        gbb_destroy(machine);
        return 2;
    }
    gbb_destroy(machine);
    return 0;
}

static int parse_mutant_mask(int argc, char **argv, uint64_t *mask) {
    *mask = 0u;
    if (argc == 3) return 0;
#ifdef GBB_P12_PUBLIC_MUTANT
    if (argc == 5 && strcmp(argv[3], "--mutants") == 0) {
        char *end = NULL;
        const unsigned long long parsed = strtoull(argv[4], &end, 0);
        if (argv[4][0] == '\0' || end == argv[4] || *end != '\0') return 1;
        *mask = (uint64_t)parsed;
        return 0;
    }
#endif
    return 1;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "probes") == 0)
        return probes(argv[2], argv[3]);
    if (argc == 4 && strcmp(argv[1], "hostile") == 0)
        return hostile(argv[2], argv[3]);
#ifdef GBB_P12_PUBLIC_MUTANT
    if (argc >= 4 && (strcmp(argv[1], "audio") == 0 || strcmp(argv[1], "frame") == 0)) {
        uint64_t mask = 0u;
        if (parse_mutant_mask(argc, argv, &mask) != 0) return 2;
        gbb_p12_set_mutants(mask);
        return digest_case(argv[1], argv[2]);
    }
#else
    if (argc == 3 && (strcmp(argv[1], "audio") == 0 || strcmp(argv[1], "frame") == 0))
        return digest_case(argv[1], argv[2]);
#endif
    fprintf(stderr, "usage: %s probes|hostile <rom> <expectations> | audio|frame <rom> [--mutants mask]\n", argv[0]);
    return 2;
}
