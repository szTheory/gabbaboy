#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define FUZZ_INPUT_LIMIT 65536u
#define FUZZ_OPERATION_LIMIT 16u
#define FUZZ_BATTERY_BYTES 8192u
#define FUZZ_IMPORT_LIMIT (FUZZ_BATTERY_BYTES + 1u)
#define FUZZ_RUN_LIMIT UINT64_C(2048)
#define FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)

static void fix_checksum(uint8_t rom[32768]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void make_battery_rom(uint8_t rom[32768]) {
    memset(rom, 0, 32768u);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    fix_checksum(rom);
}

static void require_contract(int condition) {
    if (!condition) abort();
}

static void fuzz_loader(gbb_instance *machine, const uint8_t *data, size_t size) {
    if (size <= 1u) {
        require_contract(gbb_load_rom(machine, NULL, size) == GBB_INVALID_ARGUMENT);
        return;
    }
    const gbb_error result = gbb_load_rom(machine, data + 1u, size - 1u);
    if (result != GBB_OK) {
        const gbb_run_result run = gbb_run(machine, FUZZ_RUN_LIMIT, NULL, 0u);
        require_contract(run.consumed_half_dots <= FUZZ_RUN_LIMIT);
        require_contract(run.reason == GBB_STOP_BUDGET ||
                         run.reason == GBB_STOP_UNSUPPORTED_BUS ||
                         run.reason == GBB_STOP_INVALID_STATE);
    }
}

static void fuzz_stateful_api(gbb_instance *machine, const uint8_t *data,
                              size_t size) {
    uint8_t input[FUZZ_IMPORT_LIMIT];
    uint8_t before[FUZZ_BATTERY_BYTES];
    uint8_t output[FUZZ_BATTERY_BYTES + 2u];
    size_t cursor = 1u;
    uint64_t input_half_dots = 0u;
    const size_t operations = size > 1u ?
        ((size - 1u) < FUZZ_OPERATION_LIMIT ? size - 1u : FUZZ_OPERATION_LIMIT) : 0u;

    for (size_t operation = 0u; operation < operations; ++operation) {
        const uint8_t selector = data[cursor++];
        if (selector % 6u == 0u && cursor < size) {
            size_t length = (size_t)(data[cursor++] % 32u);
            if (length > size - cursor) length = size - cursor;
            (void)gbb_load_rom(machine, data + cursor, length);
            cursor += length;
        } else if (selector % 6u == 1u) {
            size_t battery_size = 0u;
            if (gbb_battery_size(machine, &battery_size) != GBB_OK ||
                battery_size != FUZZ_BATTERY_BYTES) continue;
            size_t length = selector == 1u ? FUZZ_BATTERY_BYTES - 1u :
                            selector == 7u ? FUZZ_IMPORT_LIMIT : FUZZ_BATTERY_BYTES;
            memset(input, (int)selector, sizeof(input));
            require_contract(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
            const gbb_error imported = gbb_import_battery(machine, input, length);
            if (length != FUZZ_BATTERY_BYTES) {
                require_contract(imported == GBB_BATTERY_SIZE_MISMATCH);
                require_contract(gbb_copy_battery(machine, output + 1u,
                                                   sizeof(before)) == GBB_OK);
                require_contract(memcmp(before, output + 1u,
                                        sizeof(before)) == 0);
            } else {
                require_contract(imported == GBB_OK);
            }
        } else if (selector % 6u == 2u) {
            memset(output, 0xA7, sizeof(output));
            (void)gbb_copy_battery(machine, output + 1u,
                                   (selector & 1u) != 0u ?
                                       FUZZ_BATTERY_BYTES - 1u :
                                       sizeof(output) - 2u);
            require_contract(output[0] == 0xA7u);
            require_contract(output[sizeof(output) - 1u] == 0xA7u);
        } else if (selector % 6u == 3u) {
            uint64_t budget = (uint64_t)(selector % 32u) * 64u;
            const uint64_t remaining = FUZZ_INPUT_HALF_DOT_LIMIT - input_half_dots;
            if (budget > remaining) budget = remaining;
            const gbb_run_result run = gbb_run(machine, budget, NULL, 0u);
            require_contract(run.consumed_half_dots <= budget);
            input_half_dots += run.consumed_half_dots;
            require_contract(input_half_dots <= FUZZ_INPUT_HALF_DOT_LIMIT);
        } else if (selector % 6u == 4u) {
            (void)gbb_reset(machine);
        } else {
            size_t battery_size = SIZE_MAX;
            const gbb_error result = gbb_battery_size(machine, &battery_size);
            if (result == GBB_NO_BATTERY)
                require_contract(battery_size == SIZE_MAX);
        }
    }
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (data == NULL || size == 0u || size > FUZZ_INPUT_LIMIT) return 0;

    gbb_instance *machine = NULL;
    require_contract(gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK);
    uint8_t base_rom[32768];
    make_battery_rom(base_rom);
    require_contract(gbb_load_rom(machine, base_rom, sizeof(base_rom)) == GBB_OK);

    if ((data[0] & 1u) == 0u)
        fuzz_loader(machine, data, size);
    else
        fuzz_stateful_api(machine, data, size);

    gbb_destroy(machine);
    return 0;
}
