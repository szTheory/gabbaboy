#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Synthetic MBC2 images only: no assembled fixture, no commercial data. Bank
 * zero is never remapped on MBC2, so guest programs run straight from ROM. */

typedef struct {
    uint8_t bytes[4096];
    size_t used;
} program;

static void emit_write(program *p, uint16_t address, uint8_t value) {
    const uint8_t b[] = {0x3Eu, value, 0xEAu, (uint8_t)address, (uint8_t)(address >> 8)};
    memcpy(p->bytes + p->used, b, sizeof(b));
    p->used += sizeof(b);
}

static void emit_read_to(program *p, uint16_t address, uint16_t destination) {
    const uint8_t b[] = {0xFAu, (uint8_t)address, (uint8_t)(address >> 8),
                         0xEAu, (uint8_t)destination, (uint8_t)(destination >> 8)};
    memcpy(p->bytes + p->used, b, sizeof(b));
    p->used += sizeof(b);
}

static void emit_raw(program *p, const uint8_t *b, size_t n) {
    memcpy(p->bytes + p->used, b, n);
    p->used += n;
}

static void emit_halt(program *p) { p->bytes[p->used++] = 0x76u; }

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* Bank n carries stamp 0x40 + n at offset $1000 inside the bank. */
static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                         size_t *out_size) {
    const size_t banks = (size_t)2u << rom_code;
    *out_size = banks * 0x4000u;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    for (size_t bank = 0u; bank < banks; ++bank)
        rom[bank * 0x4000u + 0x1000u] = (uint8_t)(0x40u + bank);
    rom[0x147u] = type;
    rom[0x148u] = rom_code;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    return rom;
}

/* JP $0200 from the entry point; the program lives past the header. */
static void install(uint8_t *rom, const program *p) {
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, p->bytes, p->used);
}

static gbb_instance *new_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

/* Run in bounded slices until the guest halts; the slice cap bounds total work. */
static int run_to_halt(gbb_instance *machine) {
    for (int slice = 0; slice < 64; ++slice) {
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        if (run.reason == GBB_STOP_HALTED_IDLE) return 1;
        if (run.reason != GBB_STOP_BUDGET) return 0;
    }
    return 0;
}

static int mbc2_tracer(void) {
    size_t size = 0u;
    uint8_t *rom = make_rom(1u, 0x06u, 0u, &size); /* 64 KiB, 4 banks */
    REQUIRE(rom != NULL);
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au); /* bit 8 clear: RAM enable */
    emit_write(&p, 0xA000u, 0xA5u);
    emit_read_to(&p, 0xA200u, 0xC000u); /* echoes cell 0 */
    emit_read_to(&p, 0xBE00u, 0xC001u);
    emit_write(&p, 0x2100u, 0x02u);     /* bit 8 set: ROM bank 2 */
    emit_read_to(&p, 0x5000u, 0xC002u);
    emit_halt(&p);
    install(rom, &p);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x42u);
    size_t battery = 0u;
    REQUIRE(gbb_battery_size(machine, &battery) == GBB_OK);
    REQUIRE(battery == 512u);
    uint8_t image[512];
    REQUIRE(gbb_copy_battery(machine, image, sizeof(image)) == GBB_OK);
    REQUIRE(image[0] == 0xF5u);
    REQUIRE(run_to_halt(machine));
    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int load_program_machine(gbb_instance **out, uint8_t rom_code, uint8_t type,
                                const program *p) {
    size_t size = 0u;
    uint8_t *rom = make_rom(rom_code, type, 0u, &size);
    REQUIRE(rom != NULL);
    install(rom, p);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    free(rom);
    *out = machine;
    return 0;
}

/* After a rejected load, the previously loaded ROM must still run unchanged. */
static int previous_rom_intact(gbb_instance *machine) {
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x40u);
    return 0;
}

static int mbc2_header_matrix(void) {
    program stamp = {{0}, 0u};
    emit_read_to(&stamp, 0x1000u, 0xC000u);
    emit_halt(&stamp);
    gbb_instance *machine = NULL;
    REQUIRE(load_program_machine(&machine, 0u, 0x06u, &stamp) == 0);

    static const uint8_t types[2] = {0x05u, 0x06u};
    for (size_t t = 0u; t < 2u; ++t) {
        const uint8_t type = types[t];
        for (uint8_t rom_code = 0u; rom_code <= 3u; ++rom_code) {
            size_t size = 0u;
            uint8_t *rom = make_rom(rom_code, type, 0u, &size);
            REQUIRE(rom != NULL);
            gbb_instance *fresh = new_machine();
            REQUIRE(fresh != NULL);
            REQUIRE(gbb_load_rom(fresh, rom, size) == GBB_OK);
            gbb_destroy(fresh);

            REQUIRE(gbb_load_rom(machine, rom, size - 1u) == GBB_ROM_TRUNCATED);
            REQUIRE(previous_rom_intact(machine) == 0);
            uint8_t *longer = calloc(size + 1u, 1u);
            REQUIRE(longer != NULL);
            memcpy(longer, rom, size);
            REQUIRE(gbb_load_rom(machine, longer, size + 1u) == GBB_ROM_SIZE_MISMATCH);
            REQUIRE(previous_rom_intact(machine) == 0);
            free(longer);
            free(rom);
        }
        /* The 512 bytes come from the type row, so every RAM code but $00 is refused. */
        for (uint8_t ram_code = 1u; ram_code <= 5u; ++ram_code) {
            size_t size = 0u;
            uint8_t *rom = make_rom(0u, type, ram_code, &size);
            REQUIRE(rom != NULL);
            REQUIRE(gbb_load_rom(machine, rom, size) == GBB_UNSUPPORTED_RAM_SIZE);
            REQUIRE(previous_rom_intact(machine) == 0);
            free(rom);
        }
        /* The ROM code is checked before the shift; a 32 KiB buffer is enough. */
        for (uint8_t rom_code = 4u; rom_code <= 8u; ++rom_code) {
            size_t size = 0u;
            uint8_t *rom = make_rom(0u, type, 0u, &size);
            REQUIRE(rom != NULL);
            rom[0x148u] = rom_code;
            fix_checksum(rom);
            REQUIRE(gbb_load_rom(machine, rom, size) == GBB_UNSUPPORTED_ROM_SIZE);
            REQUIRE(previous_rom_intact(machine) == 0);
            free(rom);
        }
        const size_t too_large = (size_t)2u * 1024u * 1024u + 1u;
        uint8_t *huge = calloc(too_large, 1u);
        REQUIRE(huge != NULL);
        huge[0x147u] = type;
        huge[0x148u] = 3u;
        fix_checksum(huge);
        REQUIRE(gbb_load_rom(machine, huge, too_large) == GBB_ROM_TOO_LARGE);
        REQUIRE(previous_rom_intact(machine) == 0);
        free(huge);
    }
    gbb_destroy(machine);
    return 0;
}

/* One guest write after an optional enable-and-bank-3 prelude; the guest reports
 * the visible bank stamp, whether the RAM window answers, and the fixed bank 0. */
static int decode_case(uint16_t address, uint8_t value, int prelude) {
    program p = {{0}, 0u};
    if (prelude) {
        emit_write(&p, 0x0000u, 0x0Au);
        emit_write(&p, 0x2100u, 0x03u);
    }
    emit_write(&p, address, value);
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_read_to(&p, 0xA000u, 0xC001u);
    emit_read_to(&p, 0x1000u, 0xC002u);
    emit_halt(&p);
    gbb_instance *machine = NULL;
    REQUIRE(load_program_machine(&machine, 1u, 0x06u, &p) == 0);
    /* An all-zero image reads back as $F0, which differs from the disabled $FF. */
    uint8_t zeros[512];
    memset(zeros, 0, sizeof(zeros));
    REQUIRE(gbb_import_battery(machine, zeros, sizeof(zeros)) == GBB_OK);
    REQUIRE(run_to_halt(machine));

    int enabled = prelude;
    unsigned bank = prelude ? 3u : 1u;
    if (address < 0x4000u) {
        if ((address & 0x0100u) != 0u) {
            bank = value & 0x0Fu;
            if (bank == 0u) bank = 1u;
            bank &= 3u; /* 64 KiB: four banks */
        } else {
            enabled = (value & 0x0Fu) == 0x0Au;
        }
    }
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x40u + bank);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == (enabled ? 0xF0u : 0xFFu));
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x40u);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_register_decode(void) {
    static const uint16_t addresses[] = {0x0000u, 0x00FFu, 0x0100u, 0x01FFu, 0x1E00u,
        0x2000u, 0x20FFu, 0x2100u, 0x3EFFu, 0x3F00u, 0x3FFFu,
        0x4000u, 0x5FFFu, 0x6000u, 0x7FFFu};
    static const uint8_t values[] = {0x00u, 0x01u, 0x02u, 0x0Au, 0x0Fu, 0x1Au, 0xFAu, 0x10u};
    for (size_t a = 0u; a < sizeof(addresses) / sizeof(addresses[0]); ++a)
        for (size_t v = 0u; v < sizeof(values) / sizeof(values[0]); ++v)
            for (int prelude = 0; prelude < 2; ++prelude)
                REQUIRE(decode_case(addresses[a], values[v], prelude) == 0);

    /* Writes 0..7 to $2100 on four banks: zero translates to one, then masks. */
    program p = {{0}, 0u};
    for (uint8_t v = 0u; v < 8u; ++v) {
        emit_write(&p, 0x2100u, v);
        emit_read_to(&p, 0x5000u, (uint16_t)(0xC000u + v));
    }
    emit_halt(&p);
    gbb_instance *machine = NULL;
    REQUIRE(load_program_machine(&machine, 1u, 0x06u, &p) == 0);
    REQUIRE(run_to_halt(machine));
    static const uint8_t expected[8] = {1u, 1u, 2u, 3u, 0u, 1u, 2u, 3u};
    for (uint8_t v = 0u; v < 8u; ++v)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + v)) == 0x40u + expected[v]);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_ram_echo(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0xC000u, 0x00u);
    emit_write(&p, 0xC008u, 0x00u);
    emit_write(&p, 0x0000u, 0x0Au);
    /* Cell i := (i & 0x0F) ^ (i >> 8), written through its first 512 addresses. */
    static const uint8_t fill[] = {0x21u, 0x00u, 0xA0u, 0x7Du, 0xACu, 0xE6u, 0x0Fu,
        0x77u, 0x23u, 0x7Cu, 0xFEu, 0xA2u, 0x20u, 0xF5u};
    emit_raw(&p, fill, sizeof(fill));
    /* Flag (not count: 8192 would wrap a byte) any window address that disagrees. */
    static const uint8_t verify[] = {0x21u, 0x00u, 0xA0u, 0x7Cu, 0xE6u, 0x01u, 0xADu,
        0xE6u, 0x0Fu, 0xF6u, 0xF0u, 0x47u, 0x7Eu, 0xB8u, 0x28u, 0x05u, 0x3Eu, 0x01u,
        0xEAu, 0x00u, 0xC0u, 0x23u, 0x7Cu, 0xFEu, 0xC0u, 0x20u, 0xE8u};
    emit_raw(&p, verify, sizeof(verify));
    emit_write(&p, 0xA000u, 0xA5u);      /* canonical $F5 at cell 0 */
    emit_read_to(&p, 0xA200u, 0xC002u);
    emit_read_to(&p, 0xBE00u, 0xC003u);
    emit_write(&p, 0x0000u, 0x00u);      /* disable */
    emit_read_to(&p, 0xA000u, 0xC004u);
    emit_read_to(&p, 0xA201u, 0xC005u);
    emit_write(&p, 0xA001u, 0x0Cu);      /* ignored while disabled */
    static const uint8_t silent[] = {0x21u, 0x00u, 0xA0u, 0x7Eu, 0xFEu, 0xFFu, 0x28u,
        0x05u, 0x3Eu, 0x01u, 0xEAu, 0x08u, 0xC0u, 0x23u, 0x7Cu, 0xFEu,
        0xC0u, 0x20u, 0xF0u};
    emit_raw(&p, silent, sizeof(silent));
    emit_write(&p, 0x0000u, 0x0Au);
    emit_read_to(&p, 0xA001u, 0xC006u);
    emit_read_to(&p, 0xA000u, 0xC007u);
    emit_halt(&p);

    gbb_instance *machine = NULL;
    REQUIRE(load_program_machine(&machine, 0u, 0x05u, &p) == 0);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0u);   /* all 8192 enabled reads match */
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC005u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC008u) == 0u);   /* 8192 disabled reads are $FF */
    REQUIRE(gbb_peek_ram(machine, 0xC006u) == 0xF1u); /* the disabled write did not land */
    REQUIRE(gbb_peek_ram(machine, 0xC007u) == 0xF5u);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_reset(void) {
    program p = {{0}, 0u};
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_read_to(&p, 0xA000u, 0xC001u);
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0x2100u, 0x03u);
    emit_write(&p, 0xA000u, 0x07u);
    emit_read_to(&p, 0x5000u, 0xC002u);
    emit_read_to(&p, 0xA000u, 0xC003u);
    emit_halt(&p);
    gbb_instance *machine = NULL;
    REQUIRE(load_program_machine(&machine, 1u, 0x06u, &p) == 0);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x43u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xF7u);

    uint8_t before[512], after[512];
    uint64_t generation = 0u, generation_after = 0u;
    REQUIRE(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(gbb_copy_battery(machine, after, sizeof(after)) == GBB_OK);
    REQUIRE(memcmp(before, after, sizeof(before)) == 0);
    REQUIRE(gbb_battery_generation(machine, &generation_after) == GBB_OK);
    REQUIRE(generation_after == generation);

    /* The same program restarts: RAM is disabled again and the window is bank 1. */
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xF7u);
    gbb_destroy(machine);
    return 0;
}

static void fill_pattern(uint8_t *bytes, size_t size, uint8_t seed) {
    for (size_t i = 0u; i < size; ++i)
        bytes[i] = (uint8_t)((i * 37u + seed) & 0xFFu);
}

static gbb_instance *load_plain(uint8_t type, const program *p) {
    gbb_instance *machine = NULL;
    if (load_program_machine(&machine, 0u, type, p) != 0) return NULL;
    return machine;
}

static int mbc2_battery_image(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 0x12u);
    emit_write(&p, 0xA001u, 0x34u);
    emit_write(&p, 0xA002u, 0xFFu);
    emit_write(&p, 0xA003u, 0x00u);
    emit_write(&p, 0xBFFFu, 0x09u); /* echo address: lands on cell 0x1FF */
    emit_halt(&p);
    gbb_instance *machine = load_plain(0x06u, &p);
    REQUIRE(machine != NULL);

    size_t size = 0u;
    REQUIRE(gbb_battery_size(machine, &size) == GBB_OK);
    REQUIRE(size == 512u);
    uint8_t image[512];
    REQUIRE(gbb_copy_battery(machine, image, sizeof(image)) == GBB_OK);
    for (size_t i = 0u; i < sizeof(image); ++i) REQUIRE(image[i] == 0xFFu);

    REQUIRE(run_to_halt(machine));
    uint8_t padded[516];
    memset(padded, 0xC7, sizeof(padded));
    REQUIRE(gbb_copy_battery(machine, padded, sizeof(padded)) == GBB_OK);
    for (size_t i = 0u; i < 512u; ++i) REQUIRE((padded[i] & 0xF0u) == 0xF0u);
    for (size_t i = 512u; i < sizeof(padded); ++i) REQUIRE(padded[i] == 0xC7u);
    REQUIRE(padded[0] == 0xF2u && padded[1] == 0xF4u);
    REQUIRE(padded[2] == 0xFFu && padded[3] == 0xF0u && padded[0x1FFu] == 0xF9u);

    uint8_t small[511];
    memset(small, 0xC7, sizeof(small));
    REQUIRE(gbb_copy_battery(machine, small, sizeof(small)) == GBB_BUFFER_TOO_SMALL);
    for (size_t i = 0u; i < sizeof(small); ++i) REQUIRE(small[i] == 0xC7u);
    gbb_destroy(machine);
    return 0;
}

static gbb_instance *halt_only_machine(uint8_t type) {
    program p = {{0}, 0u};
    emit_halt(&p);
    return load_plain(type, &p);
}

static int mbc2_battery_import(void) {
    gbb_instance *machine = halt_only_machine(0x06u);
    REQUIRE(machine != NULL);
    uint8_t input[512], untouched[512], output[512];
    fill_pattern(input, sizeof(input), 0u);
    memcpy(untouched, input, sizeof(input));
    REQUIRE(gbb_import_battery(machine, input, sizeof(input)) == GBB_OK);
    REQUIRE(memcmp(input, untouched, sizeof(input)) == 0);
    REQUIRE(gbb_copy_battery(machine, output, sizeof(output)) == GBB_OK);
    for (size_t i = 0u; i < sizeof(output); ++i)
        REQUIRE(output[i] == (uint8_t)(0xF0u | (input[i] & 0x0Fu)));
    uint64_t generation = UINT64_MAX;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_battery_idempotent(void) {
    gbb_instance *machine = halt_only_machine(0x06u);
    REQUIRE(machine != NULL);
    uint8_t input[512], canonical[512];
    fill_pattern(input, sizeof(input), 5u);
    uint64_t generation = UINT64_MAX;
    REQUIRE(gbb_import_battery(machine, input, sizeof(input)) == GBB_OK);
    REQUIRE(gbb_import_battery(machine, input, sizeof(input)) == GBB_OK);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    REQUIRE(gbb_copy_battery(machine, canonical, sizeof(canonical)) == GBB_OK);
    REQUIRE(gbb_import_battery(machine, canonical, sizeof(canonical)) == GBB_OK);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    gbb_destroy(machine);

    /* Guest writes: only a changed canonical byte advances the generation. */
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 0xA5u); /* cell already $F5: no change */
    emit_write(&p, 0xA000u, 0xA6u); /* $F5 -> $F6: one advance */
    emit_write(&p, 0xA000u, 0xA6u); /* no change */
    emit_halt(&p);
    machine = load_plain(0x06u, &p);
    REQUIRE(machine != NULL);
    memset(input, 0xFF, sizeof(input));
    input[0] = 0xA5u; /* normalises to $F5 */
    REQUIRE(gbb_import_battery(machine, input, sizeof(input)) == GBB_OK);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 2u);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_battery_errors(void) {
    gbb_instance *machine = halt_only_machine(0x06u);
    REQUIRE(machine != NULL);
    uint8_t base[512], live[512], now[512], big[513];
    fill_pattern(base, sizeof(base), 9u);
    REQUIRE(gbb_import_battery(machine, base, sizeof(base)) == GBB_OK);
    REQUIRE(gbb_copy_battery(machine, live, sizeof(live)) == GBB_OK);
    fill_pattern(big, sizeof(big), 77u);

    REQUIRE(gbb_import_battery(machine, big, 0u) == GBB_BATTERY_SIZE_MISMATCH);
    REQUIRE(gbb_import_battery(machine, big, 511u) == GBB_BATTERY_SIZE_MISMATCH);
    REQUIRE(gbb_import_battery(machine, big, 513u) == GBB_BATTERY_SIZE_MISMATCH);
    REQUIRE(gbb_import_battery(NULL, big, 512u) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_import_battery(machine, NULL, 512u) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_battery(NULL, now, sizeof(now)) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_copy_battery(machine, NULL, 512u) == GBB_INVALID_ARGUMENT);
    size_t size = 0x1234u;
    uint64_t generation = 0x5678u;
    REQUIRE(gbb_battery_size(NULL, &size) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_battery_size(machine, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_battery_generation(NULL, &generation) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_battery_generation(machine, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(size == 0x1234u && generation == 0x5678u);

    /* Every rejected call left all 512 bytes and the generation as they were. */
    REQUIRE(gbb_copy_battery(machine, now, sizeof(now)) == GBB_OK);
    REQUIRE(memcmp(now, live, sizeof(now)) == 0);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    gbb_destroy(machine);
    return 0;
}

static int mbc2_battery_no_battery(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA010u, 0x07u);
    emit_read_to(&p, 0xA010u, 0xC000u);
    emit_halt(&p);
    gbb_instance *machine = load_plain(0x05u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xF7u); /* RAM is live but volatile */

    size_t size = 0x1234u;
    uint64_t generation = 0x5678u;
    uint8_t out[512], bytes[512];
    memset(out, 0xC7, sizeof(out));
    memset(bytes, 0x00, sizeof(bytes));
    REQUIRE(gbb_battery_size(machine, &size) == GBB_NO_BATTERY);
    REQUIRE(gbb_copy_battery(machine, out, sizeof(out)) == GBB_NO_BATTERY);
    REQUIRE(gbb_import_battery(machine, bytes, sizeof(bytes)) == GBB_NO_BATTERY);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_NO_BATTERY);
    REQUIRE(size == 0x1234u && generation == 0x5678u);
    for (size_t i = 0u; i < sizeof(out); ++i) REQUIRE(out[i] == 0xC7u);
    gbb_destroy(machine);
    return 0;
}

/* One ROM serves both instances. It enables RAM, fills the cells only when cell 1 still
 * reads $FF (flagging that in $C002), then dumps the 512 cells to $C100. */
static int mbc2_two_instance_roundtrip(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0xC002u, 0x00u);
    emit_write(&p, 0x0000u, 0x0Au);
    emit_read_to(&p, 0xA001u, 0xC000u);
    static const uint8_t gate[] = {0xFAu, 0x00u, 0xC0u, 0xFEu, 0xFFu, 0x20u, 0x13u};
    emit_raw(&p, gate, sizeof(gate));
    static const uint8_t fill[] = {0x21u, 0x00u, 0xA0u, 0x7Du, 0xACu, 0xE6u, 0x0Fu,
        0x77u, 0x23u, 0x7Cu, 0xFEu, 0xA2u, 0x20u, 0xF5u};
    emit_raw(&p, fill, sizeof(fill));
    emit_write(&p, 0xC002u, 0x01u);
    static const uint8_t dump[] = {0x21u, 0x00u, 0xA0u, 0x11u, 0x00u, 0xC1u,
        0x2Au, 0x12u, 0x13u, 0x7Cu, 0xFEu, 0xA2u, 0x20u, 0xF8u};
    emit_raw(&p, dump, sizeof(dump));
    emit_halt(&p);

    gbb_instance *a = load_plain(0x06u, &p);
    gbb_instance *b = load_plain(0x06u, &p);
    REQUIRE(a != NULL && b != NULL);
    REQUIRE(run_to_halt(a));
    REQUIRE(gbb_peek_ram(a, 0xC002u) == 1u); /* A filled its own empty cells */

    uint8_t image[512];
    REQUIRE(gbb_copy_battery(a, image, sizeof(image)) == GBB_OK);
    for (size_t i = 0u; i < 512u; ++i) {
        const uint8_t model = (uint8_t)(0xF0u | ((i & 0x0Fu) ^ (i >> 8)));
        REQUIRE(image[i] == model);
        REQUIRE(gbb_peek_ram(a, (uint16_t)(0xC100u + i)) == model);
    }

    uint8_t before_b[512];
    REQUIRE(gbb_copy_battery(b, before_b, sizeof(before_b)) == GBB_OK);
    for (size_t i = 0u; i < 512u; ++i) REQUIRE(before_b[i] == 0xFFu); /* independent */
    REQUIRE(gbb_import_battery(b, image, sizeof(image)) == GBB_OK);
    REQUIRE(run_to_halt(b));
    REQUIRE(gbb_peek_ram(b, 0xC002u) == 0u); /* B saw A's data and did not refill */
    for (size_t i = 0u; i < 512u; ++i)
        REQUIRE(gbb_peek_ram(b, (uint16_t)(0xC100u + i)) == image[i]);

    uint8_t after_a[512];
    uint64_t generation = 0u;
    REQUIRE(gbb_copy_battery(a, after_a, sizeof(after_a)) == GBB_OK);
    REQUIRE(memcmp(after_a, image, sizeof(image)) == 0);
    REQUIRE(gbb_battery_generation(b, &generation) == GBB_OK);
    REQUIRE(generation == 1u);
    gbb_destroy(b);
    gbb_destroy(a);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc2_tracer") == 0) return mbc2_tracer();
    if (strcmp(argv[1], "mbc2_header_matrix") == 0) return mbc2_header_matrix();
    if (strcmp(argv[1], "mbc2_register_decode") == 0) return mbc2_register_decode();
    if (strcmp(argv[1], "mbc2_ram_echo") == 0) return mbc2_ram_echo();
    if (strcmp(argv[1], "mbc2_reset") == 0) return mbc2_reset();
    if (strcmp(argv[1], "mbc2_battery_image") == 0) return mbc2_battery_image();
    if (strcmp(argv[1], "mbc2_battery_import") == 0) return mbc2_battery_import();
    if (strcmp(argv[1], "mbc2_battery_idempotent") == 0) return mbc2_battery_idempotent();
    if (strcmp(argv[1], "mbc2_battery_errors") == 0) return mbc2_battery_errors();
    if (strcmp(argv[1], "mbc2_battery_no_battery") == 0) return mbc2_battery_no_battery();
    if (strcmp(argv[1], "mbc2_two_instance_roundtrip") == 0) return mbc2_two_instance_roundtrip();
    return 2;
}
