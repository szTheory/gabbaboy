#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Synthetic MBC5 images only: no assembled fixture, no commercial data. Bank
 * zero is always mapped at $0000-$3FFF, so guest programs run straight from ROM. */

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

/* Bank n carries 0x40 + n (low byte) at offset $1000 and n >> 8 at $1001, so
 * banks 2 and 0x102 stay distinguishable on large images. */
static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                         size_t *out_size) {
    const size_t banks = (size_t)2u << rom_code;
    *out_size = banks * 0x4000u;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    for (size_t bank = 0u; bank < banks; ++bank)
    {
        rom[bank * 0x4000u + 0x1000u] = (uint8_t)(0x40u + bank);
        rom[bank * 0x4000u + 0x1001u] = (uint8_t)(bank >> 8);
    }
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

static int mbc5_tracer(void) {
    size_t size = 0u;
    uint8_t *rom = make_rom(1u, 0x19u, 0u, &size); /* 64 KiB, 4 banks */
    REQUIRE(rom != NULL);
    program p = {{0}, 0u};
    emit_write(&p, 0x2000u, 0x00u);     /* bank 0 is selectable at $4000 */
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_write(&p, 0x2000u, 0x03u);
    emit_read_to(&p, 0x5000u, 0xC001u);
    emit_read_to(&p, 0xA000u, 0xC002u); /* no RAM: mapped window reads $FF */
    emit_halt(&p);
    install(rom, &p);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x40u); /* bank 0 stamp */
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x43u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0xFFu);
    REQUIRE(run_to_halt(machine));
    gbb_destroy(machine);
    free(rom);
    return 0;
}


/* A0..FF sweep of one address: LD A,0; LD (addr),A; INC A; JR NZ. */
static void emit_sweep_write(program *p, uint16_t address) {
    const uint8_t b[] = {0x3Eu, 0x00u, 0xEAu, (uint8_t)address, (uint8_t)(address >> 8),
                         0x3Cu, 0x20u, 0xFAu};
    emit_raw(p, b, sizeof(b));
}

static gbb_instance *load_image(uint8_t *rom, size_t size, const program *p) {
    install(rom, p);
    gbb_instance *machine = new_machine();
    if (machine == NULL) return NULL;
    if (gbb_load_rom(machine, rom, size) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static gbb_instance *load_program(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                                  const program *p) {
    size_t size = 0u;
    uint8_t *rom = make_rom(rom_code, type, ram_code, &size);
    if (rom == NULL) return NULL;
    gbb_instance *machine = load_image(rom, size, p);
    free(rom);
    return machine;
}

static int previous_rom_intact(gbb_instance *machine) {
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x40u);
    return 0;
}

/* Stamps program: bank 0 stamp via $1000 into C000, then halt. */
static void stamp_program(program *p) {
    emit_read_to(p, 0x1000u, 0xC000u);
    emit_halt(p);
}

static int mbc5_header_matrix(void) {
    program stamp = {{0}, 0u};
    stamp_program(&stamp);
    gbb_instance *machine = load_program(0u, 0x19u, 0u, &stamp);
    REQUIRE(machine != NULL);

    static const uint8_t types[6] = {0x19u, 0x1Au, 0x1Bu, 0x1Cu, 0x1Du, 0x1Eu};
    static const uint8_t ram_codes[4] = {0x02u, 0x03u, 0x05u, 0x04u};
    for (uint8_t rom_code = 0u; rom_code <= 8u; ++rom_code) {
        size_t size = 0u;
        uint8_t *rom = make_rom(rom_code, 0x19u, 0u, &size);
        REQUIRE(rom != NULL);
        uint8_t *longer = NULL;
        if (rom_code <= 7u) {
            longer = calloc(size + 1u, 1u);
            REQUIRE(longer != NULL);
        }
        for (size_t t = 0u; t < 6u; ++t) {
            const uint8_t type = types[t];
            const int has_ram = type == 0x1Au || type == 0x1Bu || type == 0x1Du ||
                                type == 0x1Eu;
            rom[0x147u] = type;
            /* Every allowed RAM code loads. */
            for (size_t r = 0u; r < (has_ram ? 4u : 1u); ++r) {
                rom[0x149u] = has_ram ? ram_codes[r] : 0u;
                fix_checksum(rom);
                gbb_instance *fresh = new_machine();
                REQUIRE(fresh != NULL);
                REQUIRE(gbb_load_rom(fresh, rom, size) == GBB_OK);
                gbb_destroy(fresh);
            }
            /* Every other RAM code is refused. */
            for (unsigned code = 0u; code <= 8u; ++code) {
                int allowed = !has_ram ? code == 0u
                    : (code == 2u || code == 3u || code == 4u || code == 5u);
                if (allowed) continue;
                rom[0x149u] = (uint8_t)code;
                fix_checksum(rom);
                REQUIRE(gbb_load_rom(machine, rom, size) == GBB_UNSUPPORTED_RAM_SIZE);
            }
            rom[0x149u] = has_ram ? 0x02u : 0u;
            fix_checksum(rom);
            REQUIRE(gbb_load_rom(machine, rom, size - 1u) == GBB_ROM_TRUNCATED);
            if (longer != NULL) {
                memcpy(longer, rom, size);
                REQUIRE(gbb_load_rom(machine, longer, size + 1u) == GBB_ROM_SIZE_MISMATCH);
            }
            REQUIRE(previous_rom_intact(machine) == 0);
        }
        free(longer);
        free(rom);
    }

    /* ROM codes beyond $08 are refused before the shift; 32 KiB is enough. */
    static const uint8_t bad_codes[4] = {0x09u, 0x52u, 0x53u, 0x54u};
    for (size_t t = 0u; t < 6u; ++t) {
        for (size_t c = 0u; c < 4u; ++c) {
            size_t size = 0u;
            uint8_t *rom = make_rom(0u, types[t], 0u, &size);
            REQUIRE(rom != NULL);
            rom[0x148u] = bad_codes[c];
            fix_checksum(rom);
            REQUIRE(gbb_load_rom(machine, rom, size) == GBB_UNSUPPORTED_ROM_SIZE);
            free(rom);
        }
    }
    REQUIRE(previous_rom_intact(machine) == 0);
    gbb_destroy(machine);
    return 0;
}

static int mbc5_rom_banking(void) {
    /* 2 MiB, 128 banks: every bank by its low register. */
    program p = {{0}, 0u};
    for (unsigned bank = 0u; bank < 128u; ++bank) {
        emit_write(&p, 0x2000u, (uint8_t)bank);
        emit_read_to(&p, 0x5000u, (uint16_t)(0xC000u + bank));
    }
    emit_write(&p, 0x2000u, 0x80u);      /* masked to bank 0 */
    emit_read_to(&p, 0x5000u, 0xC100u);
    emit_write(&p, 0x2000u, 0x00u);
    emit_read_to(&p, 0x5000u, 0xC101u);
    emit_write(&p, 0x3000u, 0xFFu);      /* bit 8 set, masked away on 128 banks */
    emit_write(&p, 0x2000u, 0x05u);
    emit_read_to(&p, 0x5000u, 0xC102u);
    emit_write(&p, 0x2000u, 0x00u);
    emit_write(&p, 0x3000u, 0x00u);
    emit_write(&p, 0x2000u, 0x05u);      /* opposite order */
    emit_write(&p, 0x3000u, 0xFFu);
    emit_read_to(&p, 0x5000u, 0xC103u);
    emit_read_to(&p, 0x1000u, 0xC104u);  /* low window stays on bank 0 */
    emit_halt(&p);
    gbb_instance *machine = load_program(6u, 0x19u, 0u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (unsigned bank = 0u; bank < 128u; ++bank)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + bank)) == 0x40u + bank);
    REQUIRE(gbb_peek_ram(machine, 0xC100u) == 0x40u);
    REQUIRE(gbb_peek_ram(machine, 0xC101u) == 0x40u);
    REQUIRE(gbb_peek_ram(machine, 0xC102u) == 0x45u);
    REQUIRE(gbb_peek_ram(machine, 0xC103u) == 0x45u);
    REQUIRE(gbb_peek_ram(machine, 0xC104u) == 0x40u);
    gbb_destroy(machine);

    /* 4 MiB, 256 banks: bit 8 is masked away in both write orders. */
    program q = {{0}, 0u};
    emit_write(&q, 0x3000u, 0x01u);
    emit_write(&q, 0x2000u, 0x02u);
    emit_read_to(&q, 0x5000u, 0xC000u);
    emit_read_to(&q, 0x5001u, 0xC001u);
    emit_write(&q, 0x2000u, 0x00u);
    emit_write(&q, 0x3000u, 0x00u);
    emit_write(&q, 0x2000u, 0x02u);
    emit_write(&q, 0x3000u, 0x01u);
    emit_read_to(&q, 0x5000u, 0xC002u);
    emit_read_to(&q, 0x5001u, 0xC003u);
    emit_halt(&q);
    machine = load_program(7u, 0x19u, 0u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x42u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x00u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x42u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0x00u);
    gbb_destroy(machine);

    /* 8 MiB, 512 banks: hi=1, lo=2 reads bank $102 in both orders and a hi
     * write never clears lo. */
    program r = {{0}, 0u};
    emit_write(&r, 0x3000u, 0x01u);
    emit_write(&r, 0x2000u, 0x02u);
    emit_read_to(&r, 0x5000u, 0xC000u);
    emit_read_to(&r, 0x5001u, 0xC001u);
    emit_write(&r, 0x3000u, 0x00u);
    emit_write(&r, 0x2000u, 0x00u);
    emit_read_to(&r, 0x5000u, 0xC002u);      /* bank 0 */
    emit_write(&r, 0x2000u, 0x02u);
    emit_write(&r, 0x3000u, 0x01u);          /* opposite order */
    emit_read_to(&r, 0x5000u, 0xC003u);
    emit_read_to(&r, 0x5001u, 0xC004u);
    emit_write(&r, 0x3000u, 0x00u);          /* hi write keeps lo = 2 */
    emit_read_to(&r, 0x5000u, 0xC005u);
    emit_read_to(&r, 0x5001u, 0xC006u);
    emit_write(&r, 0x3000u, 0xFEu);          /* only value bit 0 counts */
    emit_read_to(&r, 0x5001u, 0xC007u);
    emit_halt(&r);
    machine = load_program(8u, 0x19u, 0u, &r);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x42u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x01u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x40u);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0x42u);
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0x01u);
    REQUIRE(gbb_peek_ram(machine, 0xC005u) == 0x42u);
    REQUIRE(gbb_peek_ram(machine, 0xC006u) == 0x00u);
    REQUIRE(gbb_peek_ram(machine, 0xC007u) == 0x00u);
    gbb_destroy(machine);
    return 0;
}

static int mbc5_ram_enable(void) {
    static const uint8_t values[6] = {0x0Au, 0x1Au, 0xFAu, 0x00u, 0x0Bu, 0xA0u};
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 0x5Au);
    for (size_t i = 0u; i < 6u; ++i) {
        emit_write(&p, 0x0000u, 0x00u);
        emit_write(&p, 0x0000u, values[i]);
        emit_read_to(&p, 0xA000u, (uint16_t)(0xC000u + i));
    }
    emit_write(&p, 0x0000u, 0x00u);
    emit_write(&p, 0xA000u, 0x11u);       /* disabled: ignored */
    emit_read_to(&p, 0xA000u, 0xC010u);   /* disabled: $FF */
    emit_write(&p, 0x0000u, 0x0Au);
    emit_read_to(&p, 0xA000u, 0xC011u);
    emit_halt(&p);
    gbb_instance *machine = load_program(1u, 0x1Bu, 0x02u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au); /* $0A */
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x5Au); /* $1A */
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x5Au); /* $FA */
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xFFu); /* $00 */
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0xFFu); /* $0B */
    REQUIRE(gbb_peek_ram(machine, 0xC005u) == 0xFFu); /* $A0 */
    REQUIRE(gbb_peek_ram(machine, 0xC010u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC011u) == 0x5Au);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u); /* only the enabled $5A write changed a byte */
    gbb_destroy(machine);
    return 0;
}

static int mbc5_ram_banking(void) {
    /* 128 KiB, 16 banks on a battery type without rumble: all four bits count. */
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    for (unsigned bank = 0u; bank < 16u; ++bank) {
        emit_write(&p, 0x4000u, (uint8_t)bank);
        emit_write(&p, 0xA000u, (uint8_t)(0xA0u + bank));
    }
    for (unsigned bank = 0u; bank < 16u; ++bank) {
        emit_write(&p, 0x4000u, (uint8_t)bank);
        emit_read_to(&p, 0xA000u, (uint16_t)(0xC000u + bank));
    }
    emit_write(&p, 0x4000u, 0x10u);     /* 4-bit mask: bank 0 */
    emit_read_to(&p, 0xA000u, 0xC010u);
    emit_write(&p, 0x4000u, 0x1Fu);     /* bank 15 */
    emit_read_to(&p, 0xA000u, 0xC011u);
    emit_write(&p, 0x4000u, 0x03u);     /* $6000-$7FFF writes change nothing */
    emit_sweep_write(&p, 0x6000u);
    emit_sweep_write(&p, 0x7FFFu);
    emit_read_to(&p, 0xA000u, 0xC012u);
    emit_write(&p, 0x2000u, 0x02u);
    emit_sweep_write(&p, 0x6000u);
    emit_read_to(&p, 0x5000u, 0xC013u);
    emit_halt(&p);
    gbb_instance *machine = load_program(1u, 0x1Bu, 0x04u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    for (unsigned bank = 0u; bank < 16u; ++bank)
        REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + bank)) == 0xA0u + bank);
    REQUIRE(gbb_peek_ram(machine, 0xC010u) == 0xA0u);
    REQUIRE(gbb_peek_ram(machine, 0xC011u) == 0xAFu);
    REQUIRE(gbb_peek_ram(machine, 0xC012u) == 0xA3u);
    REQUIRE(gbb_peek_ram(machine, 0xC013u) == 0x42u);
    gbb_destroy(machine);

    /* 32 KiB (4 banks): bank 5 masks to 1. 64 KiB (8 banks): 8 masks to 0, 15 to 7. */
    program q = {{0}, 0u};
    emit_write(&q, 0x0000u, 0x0Au);
    emit_write(&q, 0x4000u, 0x00u);
    emit_write(&q, 0xA000u, 0xB0u);
    emit_write(&q, 0x4000u, 0x01u);
    emit_write(&q, 0xA000u, 0xB1u);
    emit_write(&q, 0x4000u, 0x05u);
    emit_read_to(&q, 0xA000u, 0xC000u);
    emit_write(&q, 0x4000u, 0x04u);
    emit_read_to(&q, 0xA000u, 0xC001u);
    emit_halt(&q);
    machine = load_program(1u, 0x1Au, 0x03u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xB1u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xB0u);
    gbb_destroy(machine);

    program r = {{0}, 0u};
    emit_write(&r, 0x0000u, 0x0Au);
    emit_write(&r, 0x4000u, 0x00u);
    emit_write(&r, 0xA000u, 0xC0u);
    emit_write(&r, 0x4000u, 0x07u);
    emit_write(&r, 0xA000u, 0xC7u);
    emit_write(&r, 0x4000u, 0x08u);
    emit_read_to(&r, 0xA000u, 0xC000u);
    emit_write(&r, 0x4000u, 0x0Fu);
    emit_read_to(&r, 0xA000u, 0xC001u);
    emit_halt(&r);
    machine = load_program(1u, 0x1Bu, 0x05u, &r);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xC0u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xC7u);
    gbb_destroy(machine);
    return 0;
}

static int mbc5_no_ram_window(void) {
    static const uint8_t types[2] = {0x19u, 0x1Cu};
    for (size_t t = 0u; t < 2u; ++t) {
        program p = {{0}, 0u};
        emit_read_to(&p, 0xA000u, 0xC000u);
        emit_read_to(&p, 0xBFFFu, 0xC001u);
        emit_write(&p, 0x0000u, 0x0Au);
        emit_write(&p, 0xA000u, 0x11u);
        emit_read_to(&p, 0xA000u, 0xC002u);
        emit_read_to(&p, 0xB000u, 0xC003u);
        emit_halt(&p);
        gbb_instance *machine = load_program(1u, types[t], 0u, &p);
        REQUIRE(machine != NULL);
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
        for (uint16_t i = 0u; i < 4u; ++i)
            REQUIRE(gbb_peek_ram(machine, (uint16_t)(0xC000u + i)) == 0xFFu);
        uint64_t generation = 0u;
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_NO_BATTERY);
        gbb_destroy(machine);
    }
    return 0;
}

static int mbc5_battery(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0xA000u, 0x12u);
    emit_write(&p, 0xA000u, 0x12u); /* unchanged: no bump */
    emit_write(&p, 0xA000u, 0x34u);
    emit_write(&p, 0xA000u, 0x34u);
    emit_halt(&p);
    static const struct { uint8_t type, ram_code; size_t bytes; } rows[2] = {
        {0x1Bu, 0x03u, 32768u}, {0x1Eu, 0x04u, 131072u}};
    for (size_t t = 0u; t < 2u; ++t) {
        gbb_instance *machine = load_program(1u, rows[t].type, rows[t].ram_code, &p);
        REQUIRE(machine != NULL);
        size_t size = 0u;
        REQUIRE(gbb_battery_size(machine, &size) == GBB_OK);
        REQUIRE(size == rows[t].bytes);
        REQUIRE(run_to_halt(machine));
        uint64_t generation = 0u;
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
        REQUIRE(generation == 2u);
        uint8_t *image = malloc(size);
        REQUIRE(image != NULL);
        REQUIRE(gbb_copy_battery(machine, image, size) == GBB_OK);
        REQUIRE(image[0] == 0x34u && image[1] == 0xFFu);
        REQUIRE(gbb_import_battery(machine, image, size) == GBB_OK); /* identical */
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
        REQUIRE(generation == 2u);
        image[size - 1u] = 0x77u;
        REQUIRE(gbb_import_battery(machine, image, size) == GBB_OK);
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
        REQUIRE(generation == 3u);
        uint8_t *again = malloc(size);
        REQUIRE(again != NULL);
        REQUIRE(gbb_copy_battery(machine, again, size) == GBB_OK);
        REQUIRE(memcmp(image, again, size) == 0);
        free(again);
        free(image);
        gbb_destroy(machine);
    }

    static const struct { uint8_t type, ram_code; } none[4] = {
        {0x1Au, 0x02u}, {0x1Du, 0x03u}, {0x19u, 0x00u}, {0x1Cu, 0x00u}};
    for (size_t t = 0u; t < 4u; ++t) {
        gbb_instance *machine = load_program(1u, none[t].type, none[t].ram_code, &p);
        REQUIRE(machine != NULL);
        uint8_t byte = 0u;
        size_t size = 0u;
        uint64_t generation = 0u;
        REQUIRE(gbb_battery_size(machine, &size) == GBB_NO_BATTERY);
        REQUIRE(gbb_copy_battery(machine, &byte, 1u) == GBB_NO_BATTERY);
        REQUIRE(gbb_import_battery(machine, &byte, 1u) == GBB_NO_BATTERY);
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_NO_BATTERY);
        gbb_destroy(machine);
    }
    return 0;
}

static int mbc5_rom_bound(void) {
    const size_t eight_mib = (size_t)8u * 1024u * 1024u;
    program stamp = {{0}, 0u};
    stamp_program(&stamp);
    gbb_instance *previous = load_program(1u, 0x01u, 0u, &stamp);
    REQUIRE(previous != NULL);

    /* Exactly 8 MiB loads and the default bank 1 is readable. */
    program p = {{0}, 0u};
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_write(&p, 0x3000u, 0x01u);
    emit_write(&p, 0x2000u, 0xFFu);     /* the last bank, $1FF */
    emit_read_to(&p, 0x5000u, 0xC001u);
    emit_read_to(&p, 0x5001u, 0xC002u);
    emit_halt(&p);
    size_t size = 0u;
    uint8_t *rom = make_rom(8u, 0x19u, 0u, &size);
    REQUIRE(rom != NULL && size == eight_mib);
    gbb_instance *machine = load_image(rom, size, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == (uint8_t)(0x40u + 0x1FFu));
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x01u);
    gbb_destroy(machine);
    free(rom);

    /* 8 MiB + 1 and SIZE_MAX are too large for MBC5 as well. */
    uint8_t *over = calloc(eight_mib + 1u, 1u);
    REQUIRE(over != NULL);
    over[0x147u] = 0x19u;
    over[0x148u] = 8u;
    fix_checksum(over);
    REQUIRE(gbb_load_rom(previous, over, eight_mib + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_load_rom(previous, over, SIZE_MAX) == GBB_ROM_TOO_LARGE);
    REQUIRE(previous_rom_intact(previous) == 0);

    /* MBC5 code $07 at 8 MiB is a size mismatch, not too large. */
    over[0x148u] = 7u;
    fix_checksum(over);
    REQUIRE(gbb_load_rom(previous, over, eight_mib) == GBB_ROM_SIZE_MISMATCH);

    /* Every non-MBC5 type keeps the 2 MiB ceiling at the same slot. */
    static const uint8_t legacy[] = {0x00u, 0x01u, 0x03u, 0x05u, 0x06u, 0x18u, 0x20u, 0xFFu};
    for (size_t i = 0u; i < sizeof(legacy); ++i) {
        over[0x147u] = legacy[i];
        over[0x148u] = 6u;
        fix_checksum(over);
        REQUIRE(gbb_load_rom(previous, over, (size_t)2u * 1024u * 1024u + 1u) ==
                GBB_ROM_TOO_LARGE);
        REQUIRE(gbb_load_rom(previous, over, (size_t)4u * 1024u * 1024u) ==
                GBB_ROM_TOO_LARGE);
        REQUIRE(previous_rom_intact(previous) == 0);
    }
    free(over);
    gbb_destroy(previous);
    return 0;
}

static int mbc5_cgb_flag_ignored(void) {
    static const uint8_t flags[3] = {0x00u, 0x80u, 0xC0u};
    program p = {{0}, 0u};
    emit_write(&p, 0x2000u, 0x02u);
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_halt(&p);
    for (size_t i = 0u; i < 3u; ++i) {
        size_t size = 0u;
        uint8_t *rom = make_rom(1u, 0x19u, 0u, &size);
        REQUIRE(rom != NULL);
        rom[0x143u] = flags[i];
        fix_checksum(rom);
        gbb_instance *machine = load_image(rom, size, &p);
        REQUIRE(machine != NULL);
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
        REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x42u);
        gbb_destroy(machine);
        free(rom);
    }
    return 0;
}

static int mbc5_cross_mapper_control(void) {
    static const uint8_t types[3] = {0x01u, 0x19u, 0x05u};
    static const uint8_t after_zero[3] = {0x41u, 0x40u, 0x41u};
    static const uint8_t after_ten[3] = {0x41u, 0x40u, 0x42u};
    program p = {{0}, 0u};
    emit_write(&p, 0x2000u, 0x00u);
    emit_read_to(&p, 0x5000u, 0xC000u);
    emit_write(&p, 0x0100u, 0x0Au);
    emit_read_to(&p, 0x5000u, 0xC001u);
    emit_halt(&p);
    for (size_t i = 0u; i < 3u; ++i) {
        gbb_instance *machine = load_program(1u, types[i], 0u, &p);
        REQUIRE(machine != NULL);
        REQUIRE(run_to_halt(machine));
        REQUIRE(gbb_peek_ram(machine, 0xC000u) == after_zero[i]);
        REQUIRE(gbb_peek_ram(machine, 0xC001u) == after_ten[i]);
        gbb_destroy(machine);
    }
    return 0;
}

/* Run a fresh $1E (128 KiB RAM) machine through a program, return its state. */
static gbb_instance *run_rumble_program(uint8_t type, uint8_t ram_code, const program *p) {
    gbb_instance *machine = load_program(1u, type, ram_code, p);
    if (machine == NULL || !run_to_halt(machine)) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int mbc5_rumble_state(void) {
    static const uint8_t writes[4] = {0x08u, 0x0Fu, 0x07u, 0x08u};
    static const uint8_t expect_on[4] = {1u, 1u, 0u, 1u};
    static const uint64_t expect_changes[4] = {1u, 1u, 2u, 3u};
    for (size_t n = 1u; n <= 4u; ++n) {
        program p = {{0}, 0u};
        for (size_t i = 0u; i < n; ++i) emit_write(&p, 0x4000u, writes[i]);
        emit_halt(&p);
        gbb_instance *machine = run_rumble_program(0x1Eu, 0x04u, &p); /* RAM never enabled */
        REQUIRE(machine != NULL);
        uint8_t on = 0xEEu;
        uint64_t changes = 0xEEu;
        REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
        REQUIRE(on == expect_on[n - 1u]);
        REQUIRE(changes == expect_changes[n - 1u]);
        gbb_destroy(machine);
    }

    /* Bit 3 is the motor line, not a RAM bank bit: $0F selects bank 7. */
    program q = {{0}, 0u};
    emit_write(&q, 0x0000u, 0x0Au);
    emit_write(&q, 0x4000u, 0x00u);
    emit_write(&q, 0xA000u, 0x10u);
    emit_write(&q, 0x4000u, 0x07u);
    emit_write(&q, 0xA000u, 0x77u);
    emit_write(&q, 0x4000u, 0x08u);
    emit_read_to(&q, 0xA000u, 0xC000u);
    emit_write(&q, 0x4000u, 0x0Fu);
    emit_read_to(&q, 0xA000u, 0xC001u);
    emit_halt(&q);
    gbb_instance *machine = run_rumble_program(0x1Eu, 0x04u, &q);
    REQUIRE(machine != NULL);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x10u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x77u);
    uint8_t on = 0u;
    uint64_t changes = 0u;
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 1u && changes == 1u);
    gbb_destroy(machine);

    /* The non-rumble battery type keeps all four bank bits. */
    program r = {{0}, 0u};
    emit_write(&r, 0x0000u, 0x0Au);
    emit_write(&r, 0x4000u, 0x00u);
    emit_write(&r, 0xA000u, 0x10u);
    emit_write(&r, 0x4000u, 0x08u);
    emit_write(&r, 0xA000u, 0x88u);
    emit_write(&r, 0x4000u, 0x00u);
    emit_read_to(&r, 0xA000u, 0xC000u);
    emit_halt(&r);
    machine = run_rumble_program(0x1Bu, 0x04u, &r);
    REQUIRE(machine != NULL);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x10u);
    gbb_destroy(machine);
    return 0;
}

static int mbc5_rumble_errors(void) {
    REQUIRE(GBB_NO_RUMBLE == 18);
    uint8_t on = 0xA5u;
    uint64_t changes = UINT64_C(0x0123456789ABCDEF);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_rumble_state(NULL, &on, &changes) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_rumble_state(machine, NULL, &changes) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_rumble_state(machine, &on, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_NO_RUMBLE); /* no ROM */
    REQUIRE(on == 0xA5u && changes == UINT64_C(0x0123456789ABCDEF));

    program p = {{0}, 0u};
    emit_halt(&p);
    static const struct { uint8_t type, ram_code; } rows[4] = {
        {0x19u, 0x00u}, {0x1Bu, 0x02u}, {0x01u, 0x00u}, {0x05u, 0x00u}};
    for (size_t i = 0u; i < 4u; ++i) {
        size_t size = 0u;
        uint8_t *rom = make_rom(1u, rows[i].type, rows[i].ram_code, &size);
        REQUIRE(rom != NULL);
        install(rom, &p);
        REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
        free(rom);
        REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_NO_RUMBLE);
        REQUIRE(on == 0xA5u && changes == UINT64_C(0x0123456789ABCDEF));
    }
    gbb_destroy(machine);
    return 0;
}

static int mbc5_rumble_reset_load(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x4000u, 0x08u);
    emit_halt(&p);
    size_t size = 0u;
    uint8_t *rom = make_rom(1u, 0x1Cu, 0u, &size);
    REQUIRE(rom != NULL);
    install(rom, &p);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    uint8_t on = 1u;
    uint64_t changes = 9u;
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 0u && changes == 0u); /* a load never counts */

    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 1u && changes == 1u);
    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 0u && changes == 2u);
    REQUIRE(gbb_reset(machine) == GBB_OK); /* line already off: no change */
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 0u && changes == 2u);

    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 1u && changes == 3u);
    REQUIRE(gbb_load_rom(machine, rom, size - 1u) == GBB_ROM_TRUNCATED); /* failed */
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 1u && changes == 3u);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK); /* successful */
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 0u && changes == 0u);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

/* D-07: reset keeps cartridge RAM and generation but restores mapper registers. */
static int reset_preserves_ram_case(uint8_t type) {
    program tail = {{0}, 0u};
    emit_write(&tail, 0xA000u, 0x11u);                       /* RAM bank 0 */
    emit_write(&tail, 0x4000u, type == 0x1Eu ? 0x0Bu : 0x03u); /* bank 3 (+ line) */
    emit_write(&tail, 0xA000u, 0x33u);
    emit_write(&tail, 0x2000u, 0x05u);                       /* ROM bank 5 */
    program p = {{0}, 0u};
    emit_read_to(&p, 0x5000u, 0xC010u);
    emit_read_to(&p, 0xA000u, 0xC011u);
    emit_write(&p, 0x0000u, 0x0Au);
    emit_read_to(&p, 0xA000u, 0xC012u);
    const uint8_t gate[] = {0xFAu, 0x12u, 0xC0u, 0xFEu, 0x11u, 0x28u, (uint8_t)tail.used};
    emit_raw(&p, gate, sizeof(gate));
    emit_raw(&p, tail.bytes, tail.used);
    emit_halt(&p);

    gbb_instance *machine = load_program(1u, type, 0x04u, &p);
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    static uint8_t before[131072];
    static uint8_t after[131072];
    REQUIRE(gbb_copy_battery(machine, before, sizeof(before)) == GBB_OK);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 2u);
    REQUIRE(before[0] == 0x11u && before[3u * 0x2000u] == 0x33u);

    REQUIRE(gbb_reset(machine) == GBB_OK);
    REQUIRE(gbb_copy_battery(machine, after, sizeof(after)) == GBB_OK);
    REQUIRE(memcmp(before, after, sizeof(before)) == 0);
    uint64_t generation_after = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation_after) == GBB_OK);
    REQUIRE(generation_after == generation);
    if (type == 0x1Eu) {
        uint8_t on = 1u;
        uint64_t changes = 0u;
        REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
        REQUIRE(on == 0u);
    }

    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC010u) == 0x41u); /* ROM bank 1 */
    REQUIRE(gbb_peek_ram(machine, 0xC011u) == 0xFFu); /* RAM disabled */
    REQUIRE(gbb_peek_ram(machine, 0xC012u) == 0x11u); /* RAM bank 0 */
    REQUIRE(gbb_copy_battery(machine, after, sizeof(after)) == GBB_OK);
    REQUIRE(memcmp(before, after, sizeof(before)) == 0);
    REQUIRE(gbb_battery_generation(machine, &generation_after) == GBB_OK);
    REQUIRE(generation_after == generation);
    gbb_destroy(machine);
    return 0;
}

static int mbc5_reset_preserves_ram(void) {
    REQUIRE(reset_preserves_ram_case(0x1Bu) == 0);
    REQUIRE(reset_preserves_ram_case(0x1Eu) == 0);
    return 0;
}

/* ---- Original banking guest (fixtures/mbc5-banking), run through the real CPU and bus. ---- */

#define BANKING_MAX_BYTES 65536u

static uint8_t *read_banking_rom(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    uint8_t *rom = malloc(BANKING_MAX_BYTES + 1u);
    if (rom == NULL) {
        fclose(f);
        return NULL;
    }
    *size = fread(rom, 1u, BANKING_MAX_BYTES + 1u, f);
    fclose(f);
    if (*size != BANKING_MAX_BYTES) { /* the committed guest is exactly 64 KiB */
        free(rom);
        return NULL;
    }
    return rom;
}

/* Run to the guest's final HALT, bounded by the manifest timeout (half dots). */
static int run_banking_to_halt(gbb_instance *machine) {
    const gbb_run_result run = gbb_run(machine, 2000000u, NULL, 0u);
    return run.reason == GBB_STOP_HALTED_IDLE;
}

static int mbc5_banking_guest(const char *path) {
    REQUIRE(path != NULL);
    size_t size = 0u;
    uint8_t *rom = read_banking_rom(path, &size);
    REQUIRE(rom != NULL);
    REQUIRE(rom[0x147u] == 0x1Eu && rom[0x148u] == 0x01u && rom[0x149u] == 0x04u);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    REQUIRE(run_banking_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x01u); /* bank 0 in the upper window */
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0x01u); /* write orders */
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0x01u); /* RAM banking, bit 3 masked */
    REQUIRE(gbb_peek_ram(machine, 0xC005u) == 0x00u); /* $1FF not run on 64 KiB */
    REQUIRE(gbb_peek_ram(machine, 0xC001u) != 0xEEu);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xA5u);
    /* The guest's only $4000-$5FFF writes are $00..$07 (line stays off), then $0F
     * (bit 3 set: off to on, one transition), then $08 (still on, no change). */
    uint8_t on = 0u;
    uint64_t changes = 0u;
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_OK);
    REQUIRE(on == 1u);
    REQUIRE(changes == 1u);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

/* Same guest as a non-rumble $1B cartridge: all four RAM bank bits count, so
 * $0F reaches RAM bank 15 of 128 KiB. Patched in memory only. */
static int mbc5_banking_guest_1b(const char *path) {
    REQUIRE(path != NULL);
    size_t size = 0u;
    uint8_t *rom = read_banking_rom(path, &size);
    REQUIRE(rom != NULL);
    rom[0x147u] = 0x1Bu;
    fix_checksum(rom);
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    REQUIRE(run_banking_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC004u) == 0x01u); /* bank 15 reached */
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xA5u);
    uint8_t on = 1u;
    uint64_t changes = 7u;
    REQUIRE(gbb_rumble_state(machine, &on, &changes) == GBB_NO_RUMBLE);
    REQUIRE(on == 1u && changes == 7u); /* outputs untouched on error */
    gbb_destroy(machine);
    free(rom);
    return 0;
}

#define BANK_1FF_BYTES ((size_t)8u * 1024u * 1024u)
#define BANK_1FF_OFFSET ((size_t)0x1FFu * 0x4000u + 0x1000u)

/* Inflate the guest to exactly 8 MiB in memory and run it. The marker at bank
 * $1FF is harness-supplied (evidence class: synthetic oracle, not hardware).
 * Banks $101..$103 carry their low byte so the nine-bit write-order checks of
 * the guest stay valid on the larger image; bank $FF stays zero. */
static int run_bank_1ff(const char *path, uint8_t marker, uint8_t *c000, uint8_t *c001,
                        uint8_t results[4]) {
    size_t size = 0u;
    uint8_t *guest = read_banking_rom(path, &size);
    if (guest == NULL) return 0;
    uint8_t *rom = calloc(BANK_1FF_BYTES, 1u);
    if (rom == NULL) {
        free(guest);
        return 0;
    }
    memcpy(rom, guest, size);
    free(guest);
    rom[0x148u] = 0x08u;
    for (size_t bank = 0x101u; bank <= 0x103u; ++bank)
        rom[bank * 0x4000u + 0x1000u] = (uint8_t)bank;
    rom[BANK_1FF_OFFSET] = marker;
    fix_checksum(rom);

    int ok = 0;
    gbb_instance *machine = new_machine();
    if (machine != NULL && gbb_load_rom(machine, rom, BANK_1FF_BYTES) == GBB_OK
        && run_banking_to_halt(machine)) {
        *c000 = gbb_peek_ram(machine, 0xC000u);
        *c001 = gbb_peek_ram(machine, 0xC001u);
        for (uint16_t i = 0u; i < 4u; ++i) results[i] = gbb_peek_ram(machine, (uint16_t)(0xC002u + i));
        ok = 1;
    }
    if (machine != NULL) gbb_destroy(machine);
    free(rom);
    return ok;
}

static int mbc5_bank_1ff(const char *path) {
    REQUIRE(path != NULL);
    uint8_t c000 = 0u, c001 = 0u, r[4] = {0};
    REQUIRE(run_bank_1ff(path, 0x5Au, &c000, &c001, r));
    /* Order matters: under a core that drops the ninth bank bit only C005 may fail. */
    REQUIRE(r[0] == 0x01u && r[1] == 0x01u && r[2] == 0x01u); /* C002..C004 */
    REQUIRE(r[3] == 0x01u);                                   /* C005: bank $1FF in both orders */
    REQUIRE(c001 != 0xEEu);
    REQUIRE(c000 == 0xA5u);
    /* Negative control: a different marker must make the guest report failure. */
    REQUIRE(run_bank_1ff(path, 0x00u, &c000, &c001, r));
    REQUIRE(r[3] == 0xFFu);
    REQUIRE(c001 == 0xEEu);
    REQUIRE(c000 != 0xA5u);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) return 2;
    const char *path = argc == 3 ? argv[2] : NULL;
    if (strcmp(argv[1], "mbc5_tracer") == 0) return mbc5_tracer();
    if (strcmp(argv[1], "mbc5_header_matrix") == 0) return mbc5_header_matrix();
    if (strcmp(argv[1], "mbc5_rom_banking") == 0) return mbc5_rom_banking();
    if (strcmp(argv[1], "mbc5_ram_enable") == 0) return mbc5_ram_enable();
    if (strcmp(argv[1], "mbc5_ram_banking") == 0) return mbc5_ram_banking();
    if (strcmp(argv[1], "mbc5_no_ram_window") == 0) return mbc5_no_ram_window();
    if (strcmp(argv[1], "mbc5_battery") == 0) return mbc5_battery();
    if (strcmp(argv[1], "mbc5_rom_bound") == 0) return mbc5_rom_bound();
    if (strcmp(argv[1], "mbc5_cgb_flag_ignored") == 0) return mbc5_cgb_flag_ignored();
    if (strcmp(argv[1], "mbc5_cross_mapper_control") == 0) return mbc5_cross_mapper_control();
    if (strcmp(argv[1], "mbc5_rumble_state") == 0) return mbc5_rumble_state();
    if (strcmp(argv[1], "mbc5_rumble_errors") == 0) return mbc5_rumble_errors();
    if (strcmp(argv[1], "mbc5_rumble_reset_load") == 0) return mbc5_rumble_reset_load();
    if (strcmp(argv[1], "mbc5_reset_preserves_ram") == 0) return mbc5_reset_preserves_ram();
    if (strcmp(argv[1], "mbc5_banking_guest") == 0) return mbc5_banking_guest(path);
    if (strcmp(argv[1], "mbc5_banking_guest_1b") == 0) return mbc5_banking_guest_1b(path);
    if (strcmp(argv[1], "mbc5_bank_1ff") == 0) return mbc5_bank_1ff(path);
    return 2;
}
