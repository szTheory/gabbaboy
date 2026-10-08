#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

#define FUZZ_ITERATIONS 192u
#define ROM_BYTES 32768u
#define BATTERY_BYTES 8192u
#define MAX_IMPORT_BYTES (BATTERY_BYTES + 1u)
#define FUZZ_RUN_BUDGET UINT64_C(1024)

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "battery_api_fuzz failed at iteration %u: %s\n", \
            iteration, #x); return 1; \
} } while (0)

static uint32_t random_next(uint32_t *state) {
    uint32_t value = *state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    *state = value;
    return value;
}

static void fix_header_checksum(uint8_t rom[ROM_BYTES]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void make_base_rom(uint8_t rom[ROM_BYTES]) {
    memset(rom, 0, ROM_BYTES);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    fix_header_checksum(rom);
}

static void digest_u64(uint64_t *digest, uint64_t value) {
    for (unsigned byte = 0u; byte < 8u; ++byte) {
        *digest ^= (uint8_t)(value >> (byte * 8u));
        *digest *= UINT64_C(1099511628211);
    }
}

static int battery_api_fuzz(uint32_t seed, uint64_t *digest_out) {
    uint32_t random_state = seed;
    uint64_t digest = UINT64_C(1469598103934665603);
    uint8_t base_rom[ROM_BYTES];
    uint8_t candidate_rom[ROM_BYTES];
    uint8_t input[MAX_IMPORT_BYTES];
    uint8_t before[BATTERY_BYTES];
    uint8_t output[BATTERY_BYTES + 2u];
    unsigned iteration = 0u;
    make_base_rom(base_rom);

    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, base_rom, sizeof(base_rom)) == GBB_OK);

    for (; iteration < FUZZ_ITERATIONS; ++iteration) {
        REQUIRE(gbb_load_rom(machine, base_rom, sizeof(base_rom)) == GBB_OK);
        size_t battery_size = 0u;
        REQUIRE(gbb_battery_size(machine, &battery_size) == GBB_OK);
        REQUIRE(battery_size == BATTERY_BYTES);

        for (size_t i = 0u; i < sizeof(input); ++i)
            input[i] = (uint8_t)random_next(&random_state);
        size_t import_size = (size_t)(random_next(&random_state) %
                                      (MAX_IMPORT_BYTES + 1u));
        if (iteration % 8u == 0u) import_size = BATTERY_BYTES;
        if (iteration % 8u == 1u) import_size = BATTERY_BYTES - 1u;
        if (iteration % 8u == 2u) import_size = MAX_IMPORT_BYTES;

        memset(output, 0xA7, sizeof(output));
        REQUIRE(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
        uint64_t generation_before = UINT64_MAX;
        REQUIRE(gbb_battery_generation(machine, &generation_before) == GBB_OK);

        REQUIRE(gbb_import_battery(machine, input, SIZE_MAX) ==
                GBB_BATTERY_SIZE_MISMATCH);
        uint8_t after_overflow_length[BATTERY_BYTES];
        REQUIRE(gbb_copy_battery(machine, after_overflow_length,
                                 sizeof(after_overflow_length)) == GBB_OK);
        REQUIRE(memcmp(after_overflow_length, before, sizeof(before)) == 0);
        uint64_t generation_after_overflow = UINT64_MAX;
        REQUIRE(gbb_battery_generation(machine,
                &generation_after_overflow) == GBB_OK);
        REQUIRE(generation_after_overflow == generation_before);

        const gbb_error import_result =
            gbb_import_battery(machine, input, import_size);
        if (import_size == BATTERY_BYTES) {
            REQUIRE(import_result == GBB_OK);
        } else {
            REQUIRE(import_result == GBB_BATTERY_SIZE_MISMATCH);
            REQUIRE(gbb_copy_battery(machine, output + 1u,
                                     BATTERY_BYTES) == GBB_OK);
            REQUIRE(memcmp(output + 1u, before, sizeof(before)) == 0);
            uint64_t generation_after = UINT64_MAX;
            REQUIRE(gbb_battery_generation(machine, &generation_after) == GBB_OK);
            REQUIRE(generation_after == generation_before);
        }
        digest_u64(&digest, (uint64_t)import_result);
        digest_u64(&digest, import_size);
        REQUIRE(output[0] == 0xA7u);
        REQUIRE(output[sizeof(output) - 1u] == 0xA7u);

        memset(output, 0x5Cu, sizeof(output));
        REQUIRE(gbb_copy_battery(machine, output + 1u,
                                 BATTERY_BYTES + 1u) == GBB_OK);
        if (import_size == BATTERY_BYTES)
            REQUIRE(memcmp(output + 1u, input, BATTERY_BYTES) == 0);
        else
            REQUIRE(memcmp(output + 1u, before, sizeof(before)) == 0);
        REQUIRE(output[0] == 0x5Cu);
        REQUIRE(output[sizeof(output) - 1u] == 0x5Cu);

        memcpy(candidate_rom, base_rom, sizeof(candidate_rom));
        const uint32_t header_case = random_next(&random_state);
        static const uint8_t types[] = {0x01u, 0x02u, 0x03u, 0x13u};
        candidate_rom[0x147u] = types[header_case %
                                      (sizeof(types) / sizeof(types[0]))];
        candidate_rom[0x148u] = (uint8_t)((header_case >> 8) % 10u);
        candidate_rom[0x149u] = (uint8_t)((header_case >> 16) % 6u);
        fix_header_checksum(candidate_rom);
        if (iteration % 4u == 3u) candidate_rom[0x14Du] ^= 0x01u;

        uint8_t preserved[BATTERY_BYTES];
        REQUIRE(gbb_copy_battery(machine, preserved, sizeof(preserved)) == GBB_OK);
        uint64_t generation_before_load = 0u;
        REQUIRE(gbb_battery_generation(machine, &generation_before_load) == GBB_OK);
        const gbb_error load_result =
            gbb_load_rom(machine, candidate_rom, sizeof(candidate_rom));
        digest_u64(&digest, (uint64_t)load_result);
        if (load_result != GBB_OK) {
            uint8_t after_rejected_load[BATTERY_BYTES];
            REQUIRE(gbb_copy_battery(machine, after_rejected_load,
                                     sizeof(after_rejected_load)) == GBB_OK);
            REQUIRE(memcmp(after_rejected_load, preserved,
                           sizeof(preserved)) == 0);
            uint64_t generation_after_load = UINT64_MAX;
            REQUIRE(gbb_battery_generation(machine,
                    &generation_after_load) == GBB_OK);
            REQUIRE(generation_after_load == generation_before_load);
        } else {
            size_t new_size = UINT32_MAX;
            const gbb_error size_result = gbb_battery_size(machine, &new_size);
            if (size_result == GBB_OK) {
                REQUIRE(new_size == 8192u || new_size == 32768u);
                uint8_t fresh[32768];
                REQUIRE(gbb_copy_battery(machine, fresh, sizeof(fresh)) == GBB_OK);
                for (size_t i = 0u; i < new_size; ++i)
                    REQUIRE(fresh[i] == 0xFFu);
            } else {
                REQUIRE(size_result == GBB_NO_BATTERY);
                REQUIRE(new_size == UINT32_MAX);
            }
        }

        const gbb_run_result run =
            gbb_run(machine, FUZZ_RUN_BUDGET, NULL, 0u);
        digest_u64(&digest, run.consumed_half_dots);
        digest_u64(&digest, (uint64_t)run.reason);
        REQUIRE(run.consumed_half_dots <= FUZZ_RUN_BUDGET);
        REQUIRE(run.reason == GBB_STOP_BUDGET ||
                run.reason == GBB_STOP_UNSUPPORTED_BUS ||
                run.reason == GBB_STOP_INVALID_STATE);
    }

    gbb_destroy(machine);
    *digest_out = digest;
    return 0;
}

int main(void) {
    uint64_t first = 0u;
    uint64_t replay = 0u;
    if (battery_api_fuzz(UINT32_C(0x04C0FFEE), &first) != 0) return 1;
    if (battery_api_fuzz(UINT32_C(0x04C0FFEE), &replay) != 0) return 1;
    if (first != replay) {
        fprintf(stderr, "battery_api_fuzz seed replay digest mismatch\n");
        return 1;
    }
    return 0;
}
