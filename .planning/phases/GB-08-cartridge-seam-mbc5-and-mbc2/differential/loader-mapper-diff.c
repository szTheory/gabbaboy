/*
 * One-off old-versus-new differential for the Phase 8 cartridge seam (D-10).
 * Not a CTest and never built by CMake. run-differential.sh compiles this file
 * twice, once against gabbaboy.c at 5673bed and once against the working tree,
 * and diffs the two outputs. The core is included as a translation unit so the
 * static read8, write8 and read_supported can be called on either revision.
 *
 * Usage: driver [--exclude-types HEX[,HEX...]]
 */
#ifndef GBB_CORE_SOURCE
#error "define GBB_CORE_SOURCE as a quoted path to the core source under test"
#endif
#include GBB_CORE_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ROM (8u * 1024u * 1024u)
#define TWO_MIB (2u * 1024u * 1024u)

static int excluded[256];
static unsigned long cells;

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint32_t xorshift32(uint32_t *state) {
    uint32_t x = *state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return *state = x;
}

static uint64_t fnv1a64(const uint8_t *bytes, size_t n) {
    uint64_t h = 0xcbf29ce484222325ull;
    for (size_t i = 0; i < n; ++i) { h ^= bytes[i]; h *= 0x100000001b3ull; }
    return h;
}

/* Position-dependent filler so every bank reads differently. */
static void fill_pattern(uint8_t *rom, size_t size) {
    for (size_t i = 0; i < size; ++i)
        rom[i] = (uint8_t)((i * 31u) ^ (i >> 8) ^ ((i >> 14) * 7u));
}

static void loader_grid(uint8_t *buffer, const uint8_t *seed_rom) {
    static const uint8_t rom_codes[12] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 0x52, 0x53, 0x54};
    for (unsigned type = 0; type < 256u; ++type) {
        if (excluded[type]) continue;
        for (unsigned rc = 0; rc < 12u; ++rc) {
            const unsigned rom_code = rom_codes[rc];
            for (unsigned ram_code = 0; ram_code < 7u; ++ram_code) {
                const size_t declared =
                    rom_code <= 8u ? ((size_t)32768u << rom_code) : 32768u;
                const size_t lengths[4] = {declared, declared - 1u, declared + 1u,
                                           (size_t)TWO_MIB + 1u};
                for (unsigned lc = 0; lc < 4u; ++lc) {
                    memset(buffer, 0, 0x200u);
                    buffer[0x147] = (uint8_t)type;
                    buffer[0x148] = (uint8_t)rom_code;
                    buffer[0x149] = (uint8_t)ram_code;
                    fix_checksum(buffer);
                    gbb_instance *m = NULL;
                    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) exit(3);
                    if (gbb_load_rom(m, seed_rom, 32768u) != GBB_OK) exit(3);
                    const gbb_error result = gbb_load_rom(m, buffer, lengths[lc]);
                    printf("L t=%02x rc=%02x ram=%u lc=%u len=%zu -> %d r0100=%02x r0000=%02x sup=%d\n",
                           type, rom_code, ram_code, lc, lengths[lc], (int)result,
                           read8(m, 0x0100u), read8(m, 0x0000u),
                           read_supported(m, 0xA000u));
                    gbb_destroy(m);
                    ++cells;
                }
            }
        }
    }
}

static void mbc1_sequences(uint8_t *buffer) {
    for (unsigned type = 1u; type <= 3u; ++type) {
        if (excluded[type]) continue;
        for (unsigned rom_code = 0; rom_code <= 6u; ++rom_code) {
            for (unsigned ram_code = 0; ram_code <= 3u; ++ram_code) {
                const size_t size = (size_t)32768u << rom_code;
                fill_pattern(buffer, size);
                buffer[0x147] = (uint8_t)type;
                buffer[0x148] = (uint8_t)rom_code;
                buffer[0x149] = (uint8_t)ram_code;
                fix_checksum(buffer);
                gbb_instance *m = NULL;
                if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) exit(3);
                const gbb_error loaded = gbb_load_rom(m, buffer, size);
                printf("S t=%02x rc=%02x ram=%u load=%d\n", type, rom_code, ram_code,
                       (int)loaded);
                if (loaded == GBB_OK) {
                    uint32_t rng = 0x8BADF00Du;
                    for (unsigned step = 0; step < 4096u; ++step) {
                        const uint32_t r = xorshift32(&rng);
                        static const uint16_t bases[5] = {0x0000u, 0x2000u, 0x4000u,
                                                          0x6000u, 0xA000u};
                        const uint16_t addr =
                            (uint16_t)(bases[r % 5u] + ((r >> 8) & 0x1FFFu));
                        const uint8_t value = (r >> 4) % 3u == 0u
                            ? (uint8_t)0x0Au : (uint8_t)(r >> 16);
                        write8(m, addr, value);
                        printf("%u a=%04x v=%02x %02x %02x %02x %d\n", step, addr, value,
                               read8(m, (uint16_t)(r & 0x3FFFu)),
                               read8(m, (uint16_t)(0x4000u + (r & 0x3FFFu))),
                               read8(m, (uint16_t)(0xA000u + (r & 0x1FFFu))),
                               read_supported(m, 0xA000u));
                    }
                    size_t battery = 0u;
                    uint64_t generation = 0u;
                    const gbb_error be = gbb_battery_size(m, &battery);
                    const gbb_error ge = gbb_battery_generation(m, &generation);
                    uint64_t digest = 0u;
                    if (be == GBB_OK) {
                        uint8_t *copy = malloc(battery);
                        if (copy == NULL) exit(3);
                        if (gbb_copy_battery(m, copy, battery) != GBB_OK) exit(3);
                        digest = fnv1a64(copy, battery);
                        free(copy);
                    }
                    printf("B size_rc=%d size=%zu gen_rc=%d gen=%llu fnv=%016llx\n",
                           (int)be, battery, (int)ge, (unsigned long long)generation,
                           (unsigned long long)digest);
                }
                gbb_destroy(m);
                ++cells;
            }
        }
    }
}

/* A banked MBC1M candidate at 512 KiB, 1 MiB and 2 MiB, plus an uncandidated control. */
static void mbc1m_candidates(uint8_t *buffer, const uint8_t *seed_rom) {
    static const uint8_t logo[48] = {
        0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83,
        0x00, 0x0C, 0x00, 0x0D, 0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E,
        0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99, 0xBB, 0xBB, 0x67, 0x63,
        0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E};
    if (excluded[1]) return;
    for (unsigned rom_code = 4u; rom_code <= 6u; ++rom_code) {
        for (unsigned candidate = 0; candidate < 2u; ++candidate) {
            const size_t size = (size_t)32768u << rom_code;
            fill_pattern(buffer, size);
            buffer[0x147] = 0x01u;
            buffer[0x148] = (uint8_t)rom_code;
            buffer[0x149] = 0x00u;
            fix_checksum(buffer);
            if (candidate) {
                uint8_t *bank = buffer + 0x10u * 0x4000u;
                memcpy(bank + 0x104u, logo, sizeof(logo));
                bank[0x147] = 0x01u;
                fix_checksum(bank);
            }
            gbb_instance *m = NULL;
            if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) exit(3);
            if (gbb_load_rom(m, seed_rom, 32768u) != GBB_OK) exit(3);
            const gbb_error result = gbb_load_rom(m, buffer, size);
            printf("M rc=%02x candidate=%u -> %d r0100=%02x r4000=%02x\n", rom_code,
                   candidate, (int)result, read8(m, 0x0100u), read8(m, 0x4000u));
            gbb_destroy(m);
            ++cells;
        }
    }
}

int main(int argc, char **argv) {
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--exclude-types") == 0 && i + 1 < argc) {
            char *list = argv[++i];
            for (char *tok = strtok(list, ","); tok != NULL; tok = strtok(NULL, ","))
                excluded[strtol(tok, NULL, 16) & 0xFF] = 1;
        } else {
            fprintf(stderr, "usage: %s [--exclude-types HEX[,HEX...]]\n", argv[0]);
            return 2;
        }
    }
    uint8_t *buffer = calloc((size_t)MAX_ROM + 1u, 1u);
    uint8_t *seed_rom = calloc(32768u, 1u);
    if (buffer == NULL || seed_rom == NULL) return 3;
    seed_rom[0x100] = 0x42u;
    fix_checksum(seed_rom);

    loader_grid(buffer, seed_rom);
    const unsigned long grid_cells = cells;
    mbc1_sequences(buffer);
    mbc1m_candidates(buffer, seed_rom);
    printf("CELLS grid=%lu total=%lu\n", grid_cells, cells);
    free(buffer);
    free(seed_rom);
    return 0;
}
