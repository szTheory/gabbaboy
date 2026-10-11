#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Loader contradiction matrix (CART-05, D-27).
 *
 * expected_result() is an independent oracle typed from the D-27 precedence and the
 * cartridge tables in docs/cartridge-and-saves.md. It never calls or includes the core's
 * header validator; when it disagrees with gbb_load_rom the loader is fixed (or the
 * disagreement is reported), the oracle is never bent to match.
 *
 * Every rejection is made against a "guard" MBC1 $03 instance that holds an imported save,
 * and the guard is re-checked afterwards: a failed load must change nothing. */

#define KIB ((size_t)1024u)
#define MIB (KIB * KIB)
#define MAX_IMAGE (8u * MIB + 1u)

static unsigned long cases_run;

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* ---- the oracle ---------------------------------------------------------- */

typedef enum { RAM_ONLY_NONE, RAM_MBC1, RAM_MBC3, RAM_MBC5 } ram_policy;

typedef struct {
    uint8_t type;
    uint8_t max_rom_code;
    size_t ceiling;
    ram_policy ram;
    int is_mbc3;
} family_row;

static const family_row rows[] = {
    {0x00u, 0u, 2u * MIB, RAM_ONLY_NONE, 0}, {0x01u, 6u, 2u * MIB, RAM_ONLY_NONE, 0},
    {0x02u, 6u, 2u * MIB, RAM_MBC1, 0},      {0x03u, 6u, 2u * MIB, RAM_MBC1, 0},
    {0x05u, 3u, 2u * MIB, RAM_ONLY_NONE, 0}, {0x06u, 3u, 2u * MIB, RAM_ONLY_NONE, 0},
    {0x0Fu, 7u, 4u * MIB, RAM_ONLY_NONE, 1}, {0x10u, 7u, 4u * MIB, RAM_MBC3, 1},
    {0x11u, 7u, 4u * MIB, RAM_ONLY_NONE, 1}, {0x12u, 7u, 4u * MIB, RAM_MBC3, 1},
    {0x13u, 7u, 4u * MIB, RAM_MBC3, 1},      {0x19u, 8u, 8u * MIB, RAM_ONLY_NONE, 0},
    {0x1Au, 8u, 8u * MIB, RAM_MBC5, 0},      {0x1Bu, 8u, 8u * MIB, RAM_MBC5, 0},
    {0x1Cu, 8u, 8u * MIB, RAM_ONLY_NONE, 0}, {0x1Du, 8u, 8u * MIB, RAM_MBC5, 0},
    {0x1Eu, 8u, 8u * MIB, RAM_MBC5, 0},
};

static const family_row *find_row(uint8_t type) {
    for (size_t i = 0u; i < sizeof(rows) / sizeof(rows[0]); ++i)
        if (rows[i].type == type) return &rows[i];
    return NULL;
}

/* RAM code $05 on an MBC3 RAM type passes this rule so the MBC30 check can claim it later. */
static int ram_ok(const family_row *row, uint8_t rom_code, uint8_t ram_code) {
    switch (row->ram) {
    case RAM_ONLY_NONE: return ram_code == 0x00u;
    case RAM_MBC1: return ram_code == 0x02u || (ram_code == 0x03u && rom_code <= 4u);
    case RAM_MBC3: return ram_code == 0x02u || ram_code == 0x03u || ram_code == 0x05u;
    case RAM_MBC5: return ram_code >= 0x02u && ram_code <= 0x05u;
    }
    return 0;
}

static size_t declared_length(uint8_t rom_code) {
    return rom_code <= 8u ? (32u * KIB) << rom_code : 32u * KIB;
}

static gbb_error expected_result(uint8_t type, uint8_t rom_code, uint8_t ram_code,
                                 size_t length, int checksum_ok) {
    if (length > 8u * MIB) return GBB_ROM_TOO_LARGE;
    const family_row *row = find_row(type);
    if (row == NULL) return length > 2u * MIB ? GBB_ROM_TOO_LARGE : GBB_UNSUPPORTED_CARTRIDGE;
    if (length > row->ceiling) return GBB_ROM_TOO_LARGE;
    if (rom_code > row->max_rom_code) return GBB_UNSUPPORTED_ROM_SIZE;
    if (!ram_ok(row, rom_code, ram_code)) return GBB_UNSUPPORTED_RAM_SIZE;
    const size_t declared = (32u * KIB) << rom_code;
    if (length < declared) return GBB_ROM_TRUNCATED;
    if (length > declared) return GBB_ROM_SIZE_MISMATCH;
    if (!checksum_ok) return GBB_INVALID_ROM;
    if (row->is_mbc3 && (rom_code == 7u || (row->ram == RAM_MBC3 && ram_code == 5u)))
        return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
    return GBB_OK;
}

/* ---- header writer ------------------------------------------------------- */

static uint8_t *image;

static void set_header(uint8_t type, uint8_t rom_code, uint8_t ram_code, int checksum_ok) {
    memset(image + 0x100u, 0, 0x50u);
    image[0x147u] = type;
    image[0x148u] = rom_code;
    image[0x149u] = ram_code;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - image[i] - 1u);
    image[0x14Du] = checksum_ok ? checksum : (uint8_t)(checksum ^ 0x5Au);
}

/* ---- guard and twin ------------------------------------------------------ */

#define GUARD_SAVE 8192u
#define GUARD_CANARY 0x5Au

typedef struct {
    gbb_instance *machine;
    uint8_t battery[GUARD_SAVE];
    uint64_t generation;
} guard;

static gbb_instance *new_guard_machine(void) {
    static uint8_t rom[0x8000];
    static uint8_t save[GUARD_SAVE];
    memset(rom, 0, sizeof(rom));
    rom[0x147u] = 0x03u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    /* $100: JP $150.  $150: LD A,$5A ; LD ($C000),A ; JR -2 (writes the canary once). */
    const uint8_t entry[] = {0xC3u, 0x50u, 0x01u};
    const uint8_t code[] = {0x3Eu, GUARD_CANARY, 0xEAu, 0x00u, 0xC0u, 0x18u, 0xFEu};
    memcpy(rom + 0x100u, entry, sizeof(entry));
    memcpy(rom + 0x150u, code, sizeof(code));
    for (size_t i = 0u; i < sizeof(save); ++i) save[i] = (uint8_t)(i * 7u + 3u);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    if (gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK ||
        gbb_import_battery(machine, save, sizeof(save)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    (void)gbb_run(machine, 20000u, NULL, 0u);
    return machine;
}

static int snapshot(gbb_instance *machine, guard *g) {
    size_t size = 0u;
    g->machine = machine;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != GUARD_SAVE) return 0;
    if (gbb_copy_battery(machine, g->battery, sizeof(g->battery)) != GBB_OK) return 0;
    if (gbb_battery_generation(machine, &g->generation) != GBB_OK) return 0;
    return gbb_peek_ram(machine, 0xC000u) == GUARD_CANARY;
}

/* Returns 0 when the guard still equals its recorded state. */
static int guard_intact(const guard *g) {
    size_t size = 0u;
    uint8_t bytes[GUARD_SAVE];
    uint64_t generation = 0u;
    uint8_t on = 7u;
    uint64_t changes = 7u;
    if (gbb_battery_size(g->machine, &size) != GBB_OK || size != GUARD_SAVE) return 1;
    if (gbb_copy_battery(g->machine, bytes, sizeof(bytes)) != GBB_OK) return 2;
    if (memcmp(bytes, g->battery, sizeof(bytes)) != 0) return 3;
    if (gbb_battery_generation(g->machine, &generation) != GBB_OK ||
        generation != g->generation) return 4;
    if (gbb_rumble_state(g->machine, &on, &changes) != GBB_NO_RUMBLE) return 5;
    if (gbb_rtc_catch_up(g->machine, 1) != GBB_NO_RTC) return 6;
    (void)gbb_run(g->machine, 2000u, NULL, 0u);
    if (gbb_peek_ram(g->machine, 0xC000u) != GUARD_CANARY) return 7;
    return 0;
}

static gbb_instance *scratch;
static guard the_guard;

/* One checked load: the oracle picks the target (a rejection must hit the guard, an accepted
 * image goes to the scratch instance). Returns 0 on agreement. */
static int check_case(uint8_t type, uint8_t rom_code, uint8_t ram_code, size_t length,
                      int checksum_ok) {
    const gbb_error want = expected_result(type, rom_code, ram_code, length, checksum_ok);
    set_header(type, rom_code, ram_code, checksum_ok);
    gbb_instance *target = want == GBB_OK ? scratch : the_guard.machine;
    const gbb_error got = gbb_load_rom(target, image, length);
    ++cases_run;
    if (got != want) {
        fprintf(stderr,
                "mismatch: type=%02X rom_code=%02X ram_code=%02X length=%zu checksum_ok=%d "
                "oracle=%d core=%d\n",
                type, rom_code, ram_code, length, checksum_ok, (int)want, (int)got);
        return 1;
    }
    if (want != GBB_OK) {
        const int broken = guard_intact(&the_guard);
        if (broken != 0) {
            fprintf(stderr,
                    "guard changed (check %d): type=%02X rom_code=%02X ram_code=%02X length=%zu\n",
                    broken, type, rom_code, ram_code, length);
            return 1;
        }
    }
    return 0;
}

static const uint8_t rom_codes[] = {0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 0x09u, 0x52u, 0x53u,
                                    0x54u, 0xFFu};
static const uint8_t ram_codes[] = {0u, 1u, 2u, 3u, 4u, 5u, 6u, 0xFFu};

static int sweep_types(const uint8_t *types, size_t count) {
    for (size_t t = 0u; t < count; ++t)
        for (size_t r = 0u; r < sizeof(rom_codes); ++r)
            for (size_t m = 0u; m < sizeof(ram_codes); ++m) {
                const size_t base = declared_length(rom_codes[r]);
                const size_t lengths[3] = {base, base - 1u, base + 1u};
                for (int l = 0; l < 3; ++l)
                    for (int ck = 0; ck < 2; ++ck)
                        if (check_case(types[t], rom_codes[r], ram_codes[m], lengths[l], ck) != 0)
                            return 1;
            }
    return 0;
}

/* Directly asserted (not only through the oracle) so a bug mirrored in both cannot hide. */
static int must_be_ok(uint8_t type, uint8_t rom_code, uint8_t ram_code, size_t length) {
    set_header(type, rom_code, ram_code, 1);
    REQUIRE(gbb_load_rom(scratch, image, length) == GBB_OK);
    return 0;
}

static int run_family(const uint8_t *types, size_t count) {
    REQUIRE(sweep_types(types, count) == 0);
    return 0;
}

/* ---- cases --------------------------------------------------------------- */

static int loader_contradiction_mbc3(void) {
    static const uint8_t types[] = {0x0Fu, 0x10u, 0x11u, 0x12u, 0x13u};
    REQUIRE(run_family(types, sizeof(types)) == 0);
    REQUIRE(must_be_ok(0x11u, 6u, 0u, 2u * MIB) == 0); /* MBC3 code $06 at exactly 2 MiB */
    REQUIRE(must_be_ok(0x13u, 6u, 3u, 2u * MIB) == 0);
    return 0;
}

static int loader_contradiction_mbc2(void) {
    static const uint8_t types[] = {0x05u, 0x06u};
    REQUIRE(run_family(types, sizeof(types)) == 0);
    REQUIRE(must_be_ok(0x06u, 3u, 0u, 256u * KIB) == 0); /* MBC2 code $03 at exactly 256 KiB */
    REQUIRE(must_be_ok(0x05u, 3u, 0u, 256u * KIB) == 0);
    return 0;
}

static int loader_contradiction_mbc5(void) {
    static const uint8_t types[] = {0x19u, 0x1Au, 0x1Bu, 0x1Cu, 0x1Du, 0x1Eu};
    REQUIRE(run_family(types, sizeof(types)) == 0);
    REQUIRE(must_be_ok(0x19u, 8u, 0u, 8u * MIB) == 0); /* MBC5 code $08 at exactly 8 MiB */
    REQUIRE(must_be_ok(0x1Eu, 8u, 4u, 8u * MIB) == 0);
    return 0;
}

static int expect_load(uint8_t type, uint8_t rom_code, uint8_t ram_code, size_t length,
                       int checksum_ok, gbb_error want) {
    set_header(type, rom_code, ram_code, checksum_ok);
    gbb_instance *target = want == GBB_OK ? scratch : the_guard.machine;
    const gbb_error got = gbb_load_rom(target, image, length);
    ++cases_run;
    if (got != want) {
        fprintf(stderr, "type=%02X rom=%02X ram=%02X len=%zu ck=%d want=%d got=%d\n", type,
                rom_code, ram_code, length, checksum_ok, (int)want, (int)got);
        return 1;
    }
    if (want != GBB_OK && guard_intact(&the_guard) != 0) return 1;
    return 0;
}

static int loader_mbc30_variant(void) {
    /* ROM code $07 at exactly 4 MiB on every MBC3 type. */
    static const uint8_t mbc3[] = {0x0Fu, 0x10u, 0x11u, 0x12u, 0x13u};
    for (size_t i = 0u; i < sizeof(mbc3); ++i) {
        const uint8_t ram = (mbc3[i] == 0x0Fu || mbc3[i] == 0x11u) ? 0x00u : 0x03u;
        REQUIRE(expect_load(mbc3[i], 7u, ram, 4u * MIB, 1, GBB_UNSUPPORTED_CARTRIDGE_VARIANT) == 0);
        REQUIRE(expect_load(mbc3[i], 7u, ram, 4u * MIB, 0, GBB_INVALID_ROM) == 0);
        REQUIRE(expect_load(mbc3[i], 7u, ram, 4u * MIB - 1u, 1, GBB_ROM_TRUNCATED) == 0);
        REQUIRE(expect_load(mbc3[i], 7u, ram, 4u * MIB + 1u, 1, GBB_ROM_TOO_LARGE) == 0);
    }
    /* RAM code $05 (64 KiB) on the RAM-bearing types at 32 KiB. */
    static const uint8_t ram_types[] = {0x10u, 0x12u, 0x13u};
    for (size_t i = 0u; i < sizeof(ram_types); ++i) {
        REQUIRE(expect_load(ram_types[i], 0u, 5u, 32u * KIB, 1,
                            GBB_UNSUPPORTED_CARTRIDGE_VARIANT) == 0);
        REQUIRE(expect_load(ram_types[i], 0u, 5u, 32u * KIB, 0, GBB_INVALID_ROM) == 0);
    }
    /* No RAM on $0F/$11, so $05 there is an ordinary size error. */
    REQUIRE(expect_load(0x0Fu, 0u, 5u, 32u * KIB, 1, GBB_UNSUPPORTED_RAM_SIZE) == 0);
    REQUIRE(expect_load(0x11u, 0u, 5u, 32u * KIB, 1, GBB_UNSUPPORTED_RAM_SIZE) == 0);
    /* RAM $01/$04 are never candidates. */
    REQUIRE(expect_load(0x10u, 0u, 1u, 32u * KIB, 1, GBB_UNSUPPORTED_RAM_SIZE) == 0);
    REQUIRE(expect_load(0x10u, 0u, 4u, 32u * KIB, 1, GBB_UNSUPPORTED_RAM_SIZE) == 0);
    /* The same markers on other families are not MBC30. */
    REQUIRE(expect_load(0x1Bu, 0u, 5u, 32u * KIB, 1, GBB_OK) == 0);
    return 0;
}

static int loader_type_byte_sweep(void) {
    static const uint8_t accepted[] = {0x00u, 0x01u, 0x02u, 0x03u, 0x05u, 0x06u, 0x0Fu, 0x10u,
                                       0x11u, 0x12u, 0x13u, 0x19u, 0x1Au, 0x1Bu, 0x1Cu, 0x1Du,
                                       0x1Eu};
    int seen[256] = {0};
    for (unsigned type = 0u; type < 256u; ++type) {
        const family_row *row = find_row((uint8_t)type);
        uint8_t ram = 0u;
        if (row != NULL)
            while (ram < 7u && !ram_ok(row, 0u, ram)) ++ram;
        const gbb_error want = expected_result((uint8_t)type, 0u, ram, 32u * KIB, 1);
        set_header((uint8_t)type, 0u, ram, 1);
        gbb_instance *target = want == GBB_OK ? scratch : the_guard.machine;
        const gbb_error got = gbb_load_rom(target, image, 32u * KIB);
        ++cases_run;
        if (got != want) {
            fprintf(stderr, "sweep type=%02X ram=%02X oracle=%d core=%d\n", type, ram, (int)want,
                    (int)got);
            return 1;
        }
        if (got == GBB_OK) seen[type] = 1;
        else REQUIRE(guard_intact(&the_guard) == 0);
    }
    for (unsigned type = 0u; type < 256u; ++type) {
        int in_set = 0;
        for (size_t i = 0u; i < sizeof(accepted); ++i) in_set |= accepted[i] == type;
        if (seen[type] != in_set) {
            fprintf(stderr, "accepted-set mismatch at type %02X (loaded=%d expected=%d)\n", type,
                    seen[type], in_set);
            return 1;
        }
    }
    return 0;
}

static int loader_bad_checksum(void) {
    /* One probe per family at an otherwise valid header. */
    REQUIRE(expect_load(0x06u, 1u, 0u, 64u * KIB, 0, GBB_INVALID_ROM) == 0);
    REQUIRE(expect_load(0x13u, 1u, 3u, 64u * KIB, 0, GBB_INVALID_ROM) == 0);
    REQUIRE(expect_load(0x1Bu, 1u, 3u, 64u * KIB, 0, GBB_INVALID_ROM) == 0);
    REQUIRE(expect_load(0x1Bu, 1u, 3u, 64u * KIB, 1, GBB_OK) == 0);
    /* Higher-precedence errors win over a bad checksum. */
    REQUIRE(expect_load(0x13u, 1u, 3u, 64u * KIB - 1u, 0, GBB_ROM_TRUNCATED) == 0);
    REQUIRE(expect_load(0x13u, 1u, 3u, 64u * KIB + 1u, 0, GBB_ROM_SIZE_MISMATCH) == 0);
    REQUIRE(expect_load(0x13u, 1u, 6u, 64u * KIB, 0, GBB_UNSUPPORTED_RAM_SIZE) == 0);
    REQUIRE(expect_load(0x13u, 9u, 3u, 32u * KIB, 0, GBB_UNSUPPORTED_ROM_SIZE) == 0);

    /* Empty edge: no mutation of the guard on any of these. */
    set_header(0x1Bu, 0u, 3u, 1);
    REQUIRE(gbb_load_rom(the_guard.machine, NULL, 32u * KIB) == GBB_INVALID_ARGUMENT);
    REQUIRE(guard_intact(&the_guard) == 0);
    REQUIRE(gbb_load_rom(the_guard.machine, image, 0u) == GBB_INVALID_ARGUMENT);
    REQUIRE(guard_intact(&the_guard) == 0);
    REQUIRE(gbb_load_rom(the_guard.machine, image, 0x14Fu) == GBB_ROM_TRUNCATED);
    REQUIRE(guard_intact(&the_guard) == 0);
    cases_run += 3u;
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: test_loader_matrix <case>\n");
        return 2;
    }
    image = calloc(MAX_IMAGE, 1u);
    gbb_instance *twin = new_guard_machine();
    gbb_instance *guard_machine = new_guard_machine();
    if (image == NULL || twin == NULL || guard_machine == NULL ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &scratch) != GBB_OK) {
        fprintf(stderr, "setup failed\n");
        return 2;
    }
    guard twin_state;
    REQUIRE(snapshot(guard_machine, &the_guard));
    REQUIRE(snapshot(twin, &twin_state));

    int rc = 2;
    const char *name = argv[1];
    if (strcmp(name, "loader_contradiction_mbc3") == 0) rc = loader_contradiction_mbc3();
    else if (strcmp(name, "loader_contradiction_mbc2") == 0) rc = loader_contradiction_mbc2();
    else if (strcmp(name, "loader_contradiction_mbc5") == 0) rc = loader_contradiction_mbc5();
    else if (strcmp(name, "loader_mbc30_variant") == 0) rc = loader_mbc30_variant();
    else if (strcmp(name, "loader_type_byte_sweep") == 0) rc = loader_type_byte_sweep();
    else if (strcmp(name, "loader_bad_checksum") == 0) rc = loader_bad_checksum();
    else fprintf(stderr, "unknown case %s\n", name);

    if (rc == 0) {
        /* Final twin equality: every rejection left the guard equal to an untouched twin. */
        REQUIRE(guard_intact(&the_guard) == 0);
        REQUIRE(guard_intact(&twin_state) == 0);
        uint8_t a[GUARD_SAVE];
        uint8_t b[GUARD_SAVE];
        REQUIRE(gbb_copy_battery(the_guard.machine, a, sizeof(a)) == GBB_OK);
        REQUIRE(gbb_copy_battery(twin, b, sizeof(b)) == GBB_OK);
        REQUIRE(memcmp(a, b, sizeof(a)) == 0);
        REQUIRE(gbb_peek_ram(the_guard.machine, 0xC000u) == gbb_peek_ram(twin, 0xC000u));
        printf("%s cases=%lu\n", name, cases_run);
    }
    gbb_destroy(scratch);
    gbb_destroy(guard_machine);
    gbb_destroy(twin);
    free(image);
    return rc;
}
