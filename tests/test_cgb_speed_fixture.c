#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FRAME_HALF_DOTS UINT64_C(140448)
#define MAX_EXPECTATIONS 64u
#define SAMPLE_BASE 0xC100u
#define SAMPLE_STRIDE 32u
#define DONE_ADDRESS 0xC0FEu
#define REQUIRE(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "cgb-speed-fixture assertion failed: %s:%d: %s\n", \
                __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

static const char *const METRICS[] = {
    "tima", "div", "serial-lines", "serial-sc", "serial-if", "nr52-start",
    "nr52-lines", "nr52-end", "dma-159", "dma-161", "key1", "key1-armed",
    "stop-lines", "key1-after"
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

static int run_to_done(gbb_instance *machine) {
    for (unsigned frame = 0; frame < 120u; ++frame) {
        gbb_run_result result = gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u);
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
        if (read != 4 || *count == MAX_EXPECTATIONS || row.phase > 3u || row.low > row.high) {
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
    REQUIRE(run_to_done(machine) == 0);

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

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "probes") == 0)
        return probes(argv[2], argv[3]);
    fprintf(stderr, "usage: %s probes <rom> <expectations>\n", argv[0]);
    return 2;
}
