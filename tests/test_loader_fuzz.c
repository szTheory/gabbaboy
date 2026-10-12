#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ROM_BYTES (2u * 1024u * 1024u)
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* cgb_loader_fuzz_parity (Plan 10-18, D-27): a deterministic generated corpus of headers and
 * lengths, run on both profiles. gbb_probe_rom and gbb_load_rom must return the same error for
 * every entry. The same loop is then re-run with a skewed probe that answers GBB_OK for any PGB
 * $143; the loop has to notice, or the parity check itself would be vacuous. */
#define CORPUS_ROM_BYTES (128u * 1024u + 1u)

static uint32_t corpus_state = 0x9E3779B9u;
static uint32_t corpus_next(void) {   /* xorshift32: fixed seed, no host input */
    corpus_state ^= corpus_state << 13;
    corpus_state ^= corpus_state >> 17;
    corpus_state ^= corpus_state << 5;
    return corpus_state;
}

static gbb_error skewed_probe(gbb_profile profile, const uint8_t *rom, size_t size,
                              gbb_info *info) {
    if (rom != NULL && size > 0x143u && (rom[0x143u] & 0x80u) != 0u && (rom[0x143u] & 0x0Cu) != 0u)
        return GBB_OK;
    return gbb_probe_rom(profile, rom, size, info);
}

static unsigned long parity_corpus(int skew, uint8_t *rom, unsigned long *entries) {
    static const uint8_t flags[] = {0x00u, 0x80u, 0xC0u, 0x81u, 0x84u, 0x88u, 0xFFu};
    static const uint8_t types[] = {0x00u, 0x01u, 0x03u, 0x06u, 0x10u, 0x13u, 0x19u, 0x1Bu, 0x20u};
    static const size_t special[] = {0u, 1u, 0x142u, 0x143u, 0x14Fu, 0x150u, 32767u, 32768u, 32769u,
                                     65536u, 65537u};
    unsigned long mismatches = 0u;
    corpus_state = 0x9E3779B9u;
    gbb_instance *loaders[2] = {NULL, NULL};
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &loaders[0]) != GBB_OK ||
        gbb_create(GBB_PROFILE_CGB_CPU_E, &loaders[1]) != GBB_OK) abort();
    for (unsigned entry = 0u; entry < 4000u; ++entry) {
        const uint32_t a = corpus_next();
        const uint32_t b = corpus_next();
        memset(rom, 0, 0x150u);
        rom[0x143u] = (a & 0x10u) != 0u ? (uint8_t)(b >> 8) : flags[a % sizeof(flags)];
        rom[0x147u] = types[(a >> 8) % sizeof(types)];
        rom[0x148u] = (a & 0x20u) != 0u ? (uint8_t)(b >> 16) : (uint8_t)((a >> 16) % 4u);
        rom[0x149u] = (uint8_t)((a >> 24) % 7u);
        uint8_t sum = 0u;
        for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
        rom[0x14Du] = (b & 1u) != 0u ? sum : (uint8_t)(sum ^ 0x5Au);
        const size_t declared = rom[0x148u] <= 8u ? (size_t)32768u << rom[0x148u] : 32768u;
        size_t length = (b & 2u) != 0u ? special[(b >> 4) % (sizeof(special) / sizeof(special[0]))]
                                      : declared;
        if (length > CORPUS_ROM_BYTES) length = CORPUS_ROM_BYTES;
        for (int p = 0; p < 2; ++p) {
            const gbb_profile profile = p == 0 ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E;
            gbb_info info;
            memset(&info, 0, sizeof(info));
            info.struct_size = GBB_INFO_SIZE_V1;
            const gbb_error probed = skew ? skewed_probe(profile, rom, length, &info)
                                          : gbb_probe_rom(profile, rom, length, &info);
            const gbb_error loaded = gbb_load_rom(loaders[p], rom, length);
            ++*entries;
            if (probed != loaded) {
                ++mismatches;
                if (!skew)
                    fprintf(stderr, "parity: profile=%d flag=%02X type=%02X length=%zu "
                            "probe=%d load=%d\n", (int)profile, rom[0x143u], rom[0x147u], length,
                            (int)probed, (int)loaded);
            }
        }
    }
    gbb_destroy(loaders[0]);
    gbb_destroy(loaders[1]);
    return mismatches;
}

static int cgb_loader_fuzz_parity(void) {
    uint8_t *rom = calloc(CORPUS_ROM_BYTES, 1u);
    REQUIRE(rom != NULL);
    unsigned long entries = 0u;
    REQUIRE(parity_corpus(0, rom, &entries) == 0u);
    REQUIRE(entries >= 8000u);
    unsigned long skew_entries = 0u;
    const unsigned long skewed = parity_corpus(1, rom, &skew_entries);
    if (skewed == 0u) fprintf(stderr, "skewed probe went undetected\n");
    REQUIRE(skewed >= 1u);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[2], "cgb_loader_fuzz_parity") == 0)
        return cgb_loader_fuzz_parity();
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    REQUIRE(file != NULL);
    REQUIRE(fseek(file, 0, SEEK_END) == 0);
    const long fixture_size = ftell(file);
    REQUIRE(fixture_size == 32768);
    REQUIRE(fseek(file, 0, SEEK_SET) == 0);
    uint8_t fixture[32768];
    REQUIRE(fread(fixture, 1u, sizeof(fixture), file) == sizeof(fixture));
    REQUIRE(fclose(file) == 0);

    uint8_t *maximum = calloc(MAX_ROM_BYTES, 1u);
    uint8_t *over = malloc(MAX_ROM_BYTES + 1u);
    REQUIRE(maximum != NULL && over != NULL);
    memcpy(maximum, fixture, sizeof(fixture));
    maximum[0x147u] = 0x01u;
    maximum[0x148u] = 0x06u;
    maximum[0x149u] = 0x00u;
    fix_checksum(maximum);
    memcpy(over, maximum, MAX_ROM_BYTES);
    over[MAX_ROM_BYTES] = 0xA5u;

    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, fixture, sizeof(fixture)) == GBB_OK);
    REQUIRE(gbb_run(machine, 88u, NULL, 0u).consumed_half_dots == 88u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);

    REQUIRE(gbb_load_rom(machine, NULL, sizeof(fixture)) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_load_rom(machine, fixture, 0u) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_load_rom(machine, fixture, 0x14Fu) == GBB_ROM_TRUNCATED);
    REQUIRE(gbb_load_rom(machine, fixture, sizeof(fixture) - 1u) == GBB_ROM_TRUNCATED);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);

    REQUIRE(gbb_load_rom(machine, maximum, MAX_ROM_BYTES) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, over, MAX_ROM_BYTES + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_load_rom(machine, over, SIZE_MAX) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_run(machine, 4096u, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xA5u);

    gbb_destroy(machine);
    free(over);
    free(maximum);
    return 0;
}
