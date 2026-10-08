#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                         size_t *out_size) {
    *out_size = (size_t)32768u << rom_code;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    rom[0x147u] = type;
    rom[0x148u] = rom_code;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    return rom;
}

static gbb_instance *new_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

static void fill_pattern(uint8_t *bytes, size_t size, uint8_t seed) {
    for (size_t i = 0u; i < size; ++i)
        bytes[i] = (uint8_t)((i * 37u + seed) & 0xFFu);
}

static int battery_roundtrip(uint8_t rom_code, uint8_t ram_code,
                             size_t expected_size) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(rom_code, 0x03u, ram_code, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    size_t size = 0u;
    REQUIRE(gbb_battery_size(machine, &size) == GBB_OK);
    REQUIRE(size == expected_size);
    uint8_t *input = malloc(size);
    uint8_t *output = malloc(size + 4u);
    REQUIRE(input != NULL && output != NULL);
    fill_pattern(input, size, 0x31u);
    memset(output, 0xC7, size + 4u);
    REQUIRE(gbb_import_battery(machine, input, size) == GBB_OK);
    REQUIRE(gbb_copy_battery(machine, output, size + 4u) == GBB_OK);
    REQUIRE(memcmp(output, input, size) == 0);
    for (size_t i = size; i < size + 4u; ++i) REQUIRE(output[i] == 0xC7u);
    uint64_t generation = UINT64_MAX;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    REQUIRE(gbb_import_battery(machine, input, size) == GBB_OK);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    free(output);
    free(input);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int battery_errors(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(4u, 0x03u, 0x03u, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    const size_t size = 32768u;
    uint8_t *buffer = malloc(size + 1u);
    uint8_t *bad = malloc(size + 1u);
    REQUIRE(buffer != NULL && bad != NULL);
    memset(buffer, 0xA5, size + 1u);
    memset(bad, 0x5A, size + 1u);

    size_t reported_size = 0x1234u;
    REQUIRE(gbb_battery_size(machine, &reported_size) == GBB_OK);
    REQUIRE(reported_size == size);
    REQUIRE(gbb_copy_battery(machine, buffer, size - 1u) == GBB_BUFFER_TOO_SMALL);
    for (size_t i = 0u; i < size + 1u; ++i) REQUIRE(buffer[i] == 0xA5u);
    REQUIRE(gbb_import_battery(machine, bad, size - 1u) == GBB_BATTERY_SIZE_MISMATCH);
    REQUIRE(gbb_import_battery(machine, bad, size + 1u) == GBB_BATTERY_SIZE_MISMATCH);
    REQUIRE(gbb_copy_battery(machine, buffer, size + 1u) == GBB_OK);
    for (size_t i = 0u; i < size; ++i) REQUIRE(buffer[i] == 0xFFu);
    REQUIRE(buffer[size] == 0xA5u);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 0u);

    reported_size = 0x1234u;
    generation = 0x5678u;
    REQUIRE(gbb_battery_size(NULL, &reported_size) == GBB_INVALID_ARGUMENT);
    REQUIRE(reported_size == 0x1234u);
    REQUIRE(gbb_battery_size(machine, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_battery(machine, NULL, size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_battery(NULL, buffer, size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_import_battery(machine, NULL, size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_import_battery(NULL, bad, size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_battery_generation(machine, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_battery_generation(NULL, &generation) == GBB_INVALID_ARGUMENT);
    REQUIRE(generation == 0x5678u);

    free(bad);
    free(buffer);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int battery_no_battery(void) {
    const struct { uint8_t type, ram_code; } cases[] = {
        {0x00u, 0u}, /* ROM only */
        {0x01u, 0u}, /* MBC1 without RAM */
        {0x02u, 0x02u} /* volatile RAM */
    };
    uint8_t data[8192];
    memset(data, 0xA5, sizeof(data));
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        size_t rom_size = 0u;
        uint8_t *rom = make_rom(0u, cases[i].type, cases[i].ram_code, &rom_size);
        REQUIRE(rom != NULL);
        gbb_instance *machine = new_machine();
        REQUIRE(machine != NULL);
        REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
        size_t size = 0x1234u;
        REQUIRE(gbb_battery_size(machine, &size) == GBB_NO_BATTERY);
        REQUIRE(size == 0x1234u);
        REQUIRE(gbb_copy_battery(machine, data, sizeof(data)) == GBB_NO_BATTERY);
        REQUIRE(gbb_import_battery(machine, data, sizeof(data)) == GBB_NO_BATTERY);
        for (size_t j = 0u; j < sizeof(data); ++j) REQUIRE(data[j] == 0xA5u);
        gbb_destroy(machine);
        free(rom);
    }
    gbb_instance *unloaded = new_machine();
    REQUIRE(unloaded != NULL);
    size_t size = 9u;
    REQUIRE(gbb_battery_size(unloaded, &size) == GBB_NO_BATTERY);
    REQUIRE(size == 9u);
    gbb_destroy(unloaded);
    return 0;
}

static int battery_lifecycle(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(4u, 0x03u, 0x03u, &rom_size);
    REQUIRE(rom != NULL);
    static const uint8_t program[] = {
        0xFA, 0x00, 0xA0, 0xEA, 0x00, 0xC0, /* first read while disabled */
        0x3E, 0x0A, 0xEA, 0x00, 0x00,       /* enable RAM */
        0xFA, 0x00, 0xA0, 0xEA, 0x01, 0xC0, /* mode 0 reads bank zero */
        0x3E, 0x01, 0xEA, 0x00, 0x60,       /* leave mapper in mode 1 */
        0x3E, 0x02, 0xEA, 0x00, 0x40,       /* and RAM bank 2 */
        0x76
    };
    rom[0x100u] = 0xC3u; /* Keep the guest program clear of the header. */
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, program, sizeof(program));
    fix_checksum(rom);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    uint8_t initial[32768];
    memset(initial, 0xFF, sizeof(initial));
    initial[0] = 0x33u;
    initial[2u * 8192u] = 0x66u;
    REQUIRE(gbb_import_battery(machine, initial, sizeof(initial)) == GBB_OK);
    REQUIRE(gbb_run(machine, 8192u, NULL, 0u).reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x33u);
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(gbb_run(machine, 8192u, NULL, 0u).reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x33u);
    uint8_t after_reset[32768];
    REQUIRE(gbb_copy_battery(machine, after_reset, sizeof(after_reset)) == GBB_OK);
    REQUIRE(memcmp(after_reset, initial, sizeof(initial)) == 0);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);

    size_t replacement_size = 0u;
    uint8_t *replacement = make_rom(0u, 0x03u, 0x02u, &replacement_size);
    REQUIRE(replacement != NULL);
    REQUIRE(gbb_load_rom(machine, replacement, replacement_size) == GBB_OK);
    size_t battery_size = 0u;
    REQUIRE(gbb_battery_size(machine, &battery_size) == GBB_OK);
    REQUIRE(battery_size == 8192u);
    uint8_t fresh[8192];
    REQUIRE(gbb_copy_battery(machine, fresh, sizeof(fresh)) == GBB_OK);
    for (size_t i = 0u; i < sizeof(fresh); ++i) REQUIRE(fresh[i] == 0xFFu);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 0u);
    gbb_destroy(machine);
    free(replacement);
    free(rom);
    return 0;
}

static int battery_instances(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(0u, 0x03u, 0x02u, &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *first = new_machine();
    gbb_instance *second = new_machine();
    REQUIRE(first != NULL && second != NULL);
    REQUIRE(gbb_load_rom(first, rom, rom_size) == GBB_OK);
    REQUIRE(gbb_load_rom(second, rom, rom_size) == GBB_OK);
    uint8_t first_data[8192];
    uint8_t second_data[8192];
    uint8_t first_copy[8192];
    uint8_t second_copy[8192];
    fill_pattern(first_data, sizeof(first_data), 0x11u);
    fill_pattern(second_data, sizeof(second_data), 0x99u);
    REQUIRE(gbb_import_battery(first, first_data, sizeof(first_data)) == GBB_OK);
    REQUIRE(gbb_import_battery(second, second_data, sizeof(second_data)) == GBB_OK);
    REQUIRE(gbb_copy_battery(first, first_copy, sizeof(first_copy)) == GBB_OK);
    REQUIRE(gbb_copy_battery(second, second_copy, sizeof(second_copy)) == GBB_OK);
    REQUIRE(memcmp(first_copy, first_data, sizeof(first_data)) == 0);
    REQUIRE(memcmp(second_copy, second_data, sizeof(second_data)) == 0);
    gbb_destroy(second);
    gbb_destroy(first);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "battery_roundtrip8") == 0)
        return battery_roundtrip(0u, 0x02u, 8192u);
    if (strcmp(argv[1], "battery_roundtrip32") == 0)
        return battery_roundtrip(4u, 0x03u, 32768u);
    if (strcmp(argv[1], "battery_errors") == 0) return battery_errors();
    if (strcmp(argv[1], "battery_no_battery") == 0) return battery_no_battery();
    if (strcmp(argv[1], "battery_lifecycle") == 0) return battery_lifecycle();
    if (strcmp(argv[1], "battery_instances") == 0) return battery_instances();
    return 2;
}
