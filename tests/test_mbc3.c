#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Synthetic MBC3 images only: no assembled fixture, no commercial data. Bank
 * zero is never remapped, so guest programs run straight from ROM. */

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

static void emit_halt(program *p) { p->bytes[p->used++] = 0x76u; }

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* Bank n carries stamp 0x40 + n (modulo 256) at offset $1000 inside the bank. */
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

/* Run in bounded slices; the slice cap bounds total work. Returns the stop reason
 * of the final slice, or -1 when the guest never settled. */
static int run_until_stop(gbb_instance *machine) {
    for (int slice = 0; slice < 64; ++slice) {
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET) return (int)run.reason;
    }
    return -1;
}

static int run_to_halt(gbb_instance *machine) {
    return run_until_stop(machine) == (int)GBB_STOP_HALTED_IDLE;
}

static gbb_instance *load_program(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                                  const program *p) {
    size_t size = 0u;
    uint8_t *rom = make_rom(rom_code, type, ram_code, &size);
    if (rom == NULL) return NULL;
    install(rom, p);
    gbb_instance *machine = new_machine();
    if (machine != NULL && gbb_load_rom(machine, rom, size) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static int mbc3_tracer(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);     /* RAM and RTC enable */
    emit_write(&p, 0x2000u, 0x7Fu);
    emit_read_to(&p, 0x5000u, 0xC000u); /* bank 127 stamp */
    emit_write(&p, 0x2000u, 0x80u);     /* bit 7 ignored: 0, which becomes 1 */
    emit_read_to(&p, 0x5000u, 0xC001u);
    emit_write(&p, 0x4000u, 0x02u);     /* RAM bank 2 */
    emit_write(&p, 0xA123u, 0xA5u);
    emit_write(&p, 0x4000u, 0x00u);
    emit_read_to(&p, 0xA123u, 0xC002u); /* bank 0 is untouched */
    emit_write(&p, 0x4000u, 0x02u);
    emit_read_to(&p, 0xA123u, 0xC003u);
    emit_halt(&p);

    gbb_instance *machine = load_program(6u, 0x13u, 0x03u, &p); /* 2 MiB, 32 KiB RAM */
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == (uint8_t)(0x40u + 0x7Fu));
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xA5u);
    gbb_destroy(machine);
    return 0;
}

/* After a rejected load, the previously loaded ROM must still run unchanged. */
static int previous_rom_intact(gbb_instance *machine) {
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x40u);
    return 0;
}

static gbb_error try_load(gbb_instance *machine, uint8_t rom_code, uint8_t type,
                          uint8_t ram_code, size_t length_delta_minus, int grow) {
    size_t size = 0u;
    uint8_t *rom = make_rom(rom_code, type, ram_code, &size);
    if (rom == NULL) return GBB_OUT_OF_MEMORY;
    gbb_error result;
    if (grow) {
        uint8_t *bigger = realloc(rom, size + 1u);
        if (bigger == NULL) { free(rom); return GBB_OUT_OF_MEMORY; }
        bigger[size] = 0u;
        result = gbb_load_rom(machine, bigger, size + 1u);
        free(bigger);
    } else {
        result = gbb_load_rom(machine, rom, size - length_delta_minus);
        free(rom);
    }
    return result;
}

static int mbc3_header_matrix(void) {
    program stamp = {{0}, 0u};
    emit_read_to(&stamp, 0x1000u, 0xC000u);
    emit_halt(&stamp);
    gbb_instance *machine = load_program(0u, 0x13u, 0x03u, &stamp);
    REQUIRE(machine != NULL);

    for (uint8_t type = 0x0Fu; type <= 0x13u; ++type) {
        const int has_ram_rule = type == 0x10u || type == 0x12u || type == 0x13u;
        for (uint8_t ram_code = 0u; ram_code <= 6u; ++ram_code) {
            size_t size = 0u;
            uint8_t *rom = make_rom(0u, type, ram_code, &size);
            REQUIRE(rom != NULL);
            gbb_error expected = GBB_UNSUPPORTED_RAM_SIZE;
            if (!has_ram_rule && ram_code == 0u) expected = GBB_OK;
            if (has_ram_rule && (ram_code == 2u || ram_code == 3u)) expected = GBB_OK;
            if (has_ram_rule && ram_code == 5u) expected = GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
            gbb_instance *fresh = new_machine();
            REQUIRE(fresh != NULL);
            REQUIRE(gbb_load_rom(fresh, rom, size) == expected);
            gbb_destroy(fresh);
            if (expected != GBB_OK)
                REQUIRE(gbb_load_rom(machine, rom, size) == expected);
            free(rom);
        }
    }
    REQUIRE(previous_rom_intact(machine) == 0);

    /* Every row loads at the 2 MiB boundary (ROM code $06). */
    for (uint8_t type = 0x0Fu; type <= 0x13u; ++type) {
        const uint8_t ram = (type == 0x0Fu || type == 0x11u) ? 0u : 3u;
        gbb_instance *fresh = new_machine();
        REQUIRE(fresh != NULL);
        REQUIRE(try_load(fresh, 6u, type, ram, 0u, 0) == GBB_OK);
        gbb_destroy(fresh);
    }

    /* CART-05 adjacency: 2 MiB loads, 4 MiB is the MBC30 variant, 4 MiB + 1 is too large. */
    static const uint8_t timer_types[2] = {0x0Fu, 0x10u};
    for (size_t t = 0u; t < 2u; ++t) {
        const uint8_t type = timer_types[t];
        const uint8_t ram = type == 0x0Fu ? 0u : 3u;
        REQUIRE(try_load(machine, 7u, type, ram, 0u, 0) == GBB_UNSUPPORTED_CARTRIDGE_VARIANT);
        REQUIRE(try_load(machine, 7u, type, ram, 1u, 0) == GBB_ROM_TRUNCATED);
        REQUIRE(try_load(machine, 7u, type, ram, 0u, 1) == GBB_ROM_TOO_LARGE);
    }
    REQUIRE(try_load(machine, 6u, 0x13u, 3u, 0u, 1) == GBB_ROM_SIZE_MISMATCH);

    /* ROM code $08 is refused before the shift. */
    for (uint8_t type = 0x0Fu; type <= 0x13u; ++type) {
        size_t size = 0u;
        uint8_t *rom = make_rom(0u, type, 0u, &size);
        REQUIRE(rom != NULL);
        rom[0x148u] = 0x08u;
        fix_checksum(rom);
        REQUIRE(gbb_load_rom(machine, rom, size) == GBB_UNSUPPORTED_ROM_SIZE);
        free(rom);
    }

    /* Types $08 and $09 remain outside the matrix. */
    for (uint8_t type = 0x08u; type <= 0x09u; ++type)
        REQUIRE(try_load(machine, 0u, type, 0u, 0u, 0) == GBB_UNSUPPORTED_CARTRIDGE);

    /* The checksum is checked before the variant: a bad one on an MBC30 header is INVALID_ROM. */
    {
        size_t size = 0u;
        uint8_t *rom = make_rom(7u, 0x13u, 3u, &size);
        REQUIRE(rom != NULL);
        rom[0x14Du] ^= 0x01u;
        REQUIRE(gbb_load_rom(machine, rom, size) == GBB_INVALID_ROM);
        free(rom);
        rom = make_rom(0u, 0x13u, 5u, &size);
        REQUIRE(rom != NULL);
        rom[0x14Du] ^= 0x01u;
        REQUIRE(gbb_load_rom(machine, rom, size) == GBB_INVALID_ROM);
        free(rom);
    }
    REQUIRE(previous_rom_intact(machine) == 0);
    gbb_destroy(machine);
    return 0;
}

static int mbc3_rom_banking(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    for (uint8_t bank = 1u; bank < 128u; ++bank) {
        emit_write(&p, 0x2000u, bank);
        emit_read_to(&p, 0x5000u, (uint16_t)(0xC000u + bank));
    }
    emit_write(&p, 0x2000u, 0x00u);     /* 0 becomes 1 */
    emit_read_to(&p, 0x5000u, 0xC100u);
    emit_write(&p, 0x2000u, 0x85u);     /* bit 7 ignored: bank 5 */
    emit_read_to(&p, 0x5000u, 0xC101u);
    emit_read_to(&p, 0x1000u, 0xC102u); /* $0000-$3FFF is always bank 0 */
    emit_halt(&p);
    gbb_instance *machine = load_program(6u, 0x11u, 0u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (uint8_t bank = 1u; bank < 128u; ++bank)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + bank)) == (uint8_t)(0x40u + bank));
    REQUIRE(gbb_peek_ram(machine, 0xC100u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC101u) == 0x45u);
    REQUIRE(gbb_peek_ram(machine, 0xC102u) == 0x40u);
    gbb_destroy(machine);

    /* 256 KiB image, 16 banks: translate zero first, then mask (D-03). */
    program q = {{0}, 0u};
    emit_write(&q, 0x2000u, 0x7Fu);     /* 127 & 15 = 15 */
    emit_read_to(&q, 0x5000u, 0xC000u);
    emit_write(&q, 0x2000u, 0x10u);     /* 16 is not zero, so 16 & 15 = bank 0 */
    emit_read_to(&q, 0x5000u, 0xC001u);
    emit_write(&q, 0x2000u, 0x00u);     /* zero becomes one */
    emit_read_to(&q, 0x5000u, 0xC002u);
    emit_halt(&q);
    machine = load_program(3u, 0x11u, 0u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x4Fu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x40u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x41u);
    gbb_destroy(machine);
    return 0;
}

static int mbc3_ram_banking(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    for (uint8_t bank = 0u; bank < 4u; ++bank) {
        emit_write(&p, 0x4000u, bank);
        emit_write(&p, 0xA000u, (uint8_t)(0x10u + bank));
        emit_write(&p, 0xBFFFu, (uint8_t)(0x20u + bank));
    }
    for (uint8_t bank = 0u; bank < 4u; ++bank) {
        emit_write(&p, 0x4000u, bank);
        emit_read_to(&p, 0xA000u, (uint16_t)(0xC000u + bank));
        emit_read_to(&p, 0xBFFFu, (uint16_t)(0xC010u + bank));
    }
    emit_halt(&p);
    gbb_instance *machine = load_program(0u, 0x13u, 0x03u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (uint8_t bank = 0u; bank < 4u; ++bank) {
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + bank)) == (uint8_t)(0x10u + bank));
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC010u + bank)) == (uint8_t)(0x20u + bank));
    }
    gbb_destroy(machine);

    /* 8 KiB cart: selections 1-3 alias bank 0. */
    program q = {{0}, 0u};
    emit_write(&q, 0x0000u, 0x0Au);
    emit_write(&q, 0x4000u, 0x01u);
    emit_write(&q, 0xA010u, 0x77u);
    emit_write(&q, 0x4000u, 0x02u);
    emit_read_to(&q, 0xA010u, 0xC000u);
    emit_write(&q, 0x4000u, 0x03u);
    emit_read_to(&q, 0xA010u, 0xC001u);
    emit_write(&q, 0x4000u, 0x00u);
    emit_read_to(&q, 0xA010u, 0xC002u);
    emit_write(&q, 0x4000u, 0x03u);
    emit_write(&q, 0xA020u, 0x88u);
    emit_write(&q, 0x4000u, 0x00u);
    emit_read_to(&q, 0xA020u, 0xC003u);
    emit_halt(&q);
    machine = load_program(0u, 0x13u, 0x02u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x77u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x77u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x77u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0x88u);
    gbb_destroy(machine);
    return 0;
}

static int mbc3_ram_gate(void) {
    program p = {{0}, 0u};
    emit_read_to(&p, 0xA000u, 0xC000u);   /* disabled after load: $FF */
    emit_write(&p, 0xA000u, 0x12u);       /* ignored */
    emit_write(&p, 0x0000u, 0x1Au);       /* low nibble $A enables */
    emit_read_to(&p, 0xA000u, 0xC001u);   /* the ignored write left $FF */
    emit_write(&p, 0xA000u, 0x34u);
    emit_read_to(&p, 0xA000u, 0xC002u);
    emit_write(&p, 0x0000u, 0x0Bu);       /* disable */
    emit_read_to(&p, 0xA000u, 0xC003u);
    emit_write(&p, 0xA000u, 0x56u);       /* ignored */
    emit_write(&p, 0x0000u, 0x0Au);
    emit_read_to(&p, 0xA000u, 0xC004u);
    emit_write(&p, 0x0000u, 0x00u);       /* disable */
    emit_read_to(&p, 0xA000u, 0xC005u);
    emit_write(&p, 0x0000u, 0xAAu);       /* low nibble $A enables (D-03 decode) */
    emit_read_to(&p, 0xA000u, 0xC006u);
    emit_halt(&p);
    gbb_instance *machine = load_program(0u, 0x13u, 0x03u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x34u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0x34u);
    REQUIRE(gbb_peek_ram(machine, 0xC005u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC006u) == 0x34u);
    uint8_t image[32768];
    REQUIRE(gbb_copy_battery(machine, image, sizeof(image)) == GBB_OK);
    REQUIRE(image[0] == 0x34u);
    for (size_t i = 1u; i < sizeof(image); ++i) REQUIRE(image[i] == 0xFFu);
    gbb_destroy(machine);
    return 0;
}

/* Selections with no mapped target read $FF and ignore writes. */
static int unmapped_program(program *p, const uint8_t *selections, size_t count) {
    emit_write(p, 0x0000u, 0x0Au);
    emit_write(p, 0x4000u, 0x00u);
    emit_write(p, 0xA000u, 0x55u);
    for (size_t i = 0u; i < count; ++i) {
        emit_write(p, 0x4000u, selections[i]);
        emit_read_to(p, 0xA000u, (uint16_t)(0xC000u + i));
        emit_write(p, 0xA000u, 0x99u);
    }
    emit_write(p, 0x4000u, 0x00u);
    emit_read_to(p, 0xA000u, 0xC0F0u);
    emit_halt(p);
    return 0;
}

static int mbc3_unmapped_select(void) {
    static const uint8_t no_timer_sel[] = {0x04u, 0x05u, 0x06u, 0x07u, 0x08u, 0x09u,
                                           0x0Au, 0x0Bu, 0x0Cu, 0x0Du, 0x80u, 0xFFu};
    program p = {{0}, 0u};
    unmapped_program(&p, no_timer_sel, sizeof(no_timer_sel));
    static const uint8_t ram_types[2] = {0x12u, 0x13u};
    for (size_t t = 0u; t < 2u; ++t) {
        gbb_instance *machine = load_program(0u, ram_types[t], 0x03u, &p);
        REQUIRE(machine != NULL);
        REQUIRE(run_to_halt(machine));
        for (size_t i = 0u; i < sizeof(no_timer_sel); ++i)
            REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + i)) == 0xFFu);
        /* The ignored $99 writes never landed; a later $00 selection reads the real byte. */
        REQUIRE(gbb_peek_ram(machine, 0xC0F0u) == 0x55u);
        gbb_destroy(machine);
    }

    /* $11 has no RAM at all: selections $08-$0C read $FF as well. */
    program q = {{0}, 0u};
    unmapped_program(&q, no_timer_sel, sizeof(no_timer_sel));
    gbb_instance *machine = load_program(0u, 0x11u, 0u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (size_t i = 0u; i < sizeof(no_timer_sel); ++i)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + i)) == 0xFFu);
    gbb_destroy(machine);

    /* Timer types ($10) share the RAM-only selections $04-$07 and $0D-$FF. */
    static const uint8_t timer_sel[] = {0x04u, 0x05u, 0x06u, 0x07u, 0x0Du, 0x80u, 0xFFu};
    program r = {{0}, 0u};
    unmapped_program(&r, timer_sel, sizeof(timer_sel));
    machine = load_program(0u, 0x10u, 0x03u, &r);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (size_t i = 0u; i < sizeof(timer_sel); ++i)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + i)) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC0F0u) == 0x55u);
    gbb_destroy(machine);
    return 0;
}

static int mbc3_absent_ram(void) {
    static const uint8_t types[2] = {0x0Fu, 0x11u};
    for (size_t t = 0u; t < 2u; ++t) {
        program p = {{0}, 0u};
        emit_write(&p, 0x0000u, 0x0Au);
        emit_read_to(&p, 0xA000u, 0xC000u);
        emit_write(&p, 0xA000u, 0x12u);
        emit_read_to(&p, 0xBFFFu, 0xC001u);
        emit_halt(&p);
        gbb_instance *machine = load_program(0u, types[t], 0u, &p);
        REQUIRE(machine != NULL);
        REQUIRE(run_until_stop(machine) == (int)GBB_STOP_HALTED_IDLE);
        REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
        REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
        size_t battery = 0u;
        if (types[t] == 0x0Fu) {
            /* No RAM, but a timer and battery: the image is the 21-byte clock block. */
            REQUIRE(gbb_battery_size(machine, &battery) == GBB_OK);
            REQUIRE(battery == GBB_RTC_BLOCK_SIZE);
        } else {
            REQUIRE(gbb_battery_size(machine, &battery) == GBB_NO_BATTERY);
        }
        gbb_destroy(machine);
    }
    return 0;
}

static int mbc3_reset(void) {
    program p = {{0}, 0u};
    emit_read_to(&p, 0x5000u, 0xC000u);   /* probes see the state at reset */
    emit_read_to(&p, 0xA000u, 0xC001u);
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0x2000u, 0x05u);
    emit_write(&p, 0x4000u, 0x02u);
    emit_write(&p, 0xA000u, 0xC3u);
    emit_halt(&p);
    gbb_instance *machine = load_program(3u, 0x13u, 0x03u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    uint8_t image[32768];
    REQUIRE(gbb_copy_battery(machine, image, sizeof(image)) == GBB_OK);
    REQUIRE(image[2u * 0x2000u] == 0xC3u);
    REQUIRE(run_to_halt(machine));
    /* Bank 1, RAM bank 0 and RAM disabled again: stale registers would read $45 and $C3. */
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);          /* identical rewrite does not bump */
    gbb_destroy(machine);
    return 0;
}

static int mbc3_battery_generation(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0xA000u, 0x11u);       /* disabled: no change */
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 0x11u);       /* +1 */
    emit_write(&p, 0xA000u, 0x11u);       /* identical */
    emit_write(&p, 0xA001u, 0x22u);       /* +1 */
    emit_write(&p, 0xA002u, 0xFFu);       /* identical to the fresh $FF */
    emit_halt(&p);
    gbb_instance *machine = load_program(0u, 0x13u, 0x03u, &p);
    REQUIRE(machine != NULL);
    uint64_t generation = UINT64_MAX;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 0u);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 2u);
    gbb_destroy(machine);

    /* $12 has volatile RAM and no battery. */
    machine = load_program(0u, 0x12u, 0x03u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    generation = 7u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_NO_BATTERY);
    REQUIRE(generation == 7u);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc3_tracer") == 0) return mbc3_tracer();
    if (strcmp(argv[1], "mbc3_header_matrix") == 0) return mbc3_header_matrix();
    if (strcmp(argv[1], "mbc3_rom_banking") == 0) return mbc3_rom_banking();
    if (strcmp(argv[1], "mbc3_ram_banking") == 0) return mbc3_ram_banking();
    if (strcmp(argv[1], "mbc3_ram_gate") == 0) return mbc3_ram_gate();
    if (strcmp(argv[1], "mbc3_unmapped_select") == 0) return mbc3_unmapped_select();
    if (strcmp(argv[1], "mbc3_absent_ram") == 0) return mbc3_absent_ram();
    if (strcmp(argv[1], "mbc3_reset") == 0) return mbc3_reset();
    if (strcmp(argv[1], "mbc3_battery_generation") == 0) return mbc3_battery_generation();
    return 2;
}
