#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* CGB profile API: gbb_probe_rom, gbb_get_info and the PGB rejection (CGB-01, D-01..D-04).
 *
 * expected_result() is an independent oracle typed from the loader matrix (CART-05) plus the
 * D-03 PGB term appended last. It never calls the core's header validator. When it disagrees
 * with the core, the core is fixed (or the disagreement is reported); the oracle is never bent
 * to match. The $143 support table below is written out as literals for the same reason.
 *
 * gbb_create accepts both profiles (Plan 10-06), so the parity loop compares probe to a real
 * gbb_load_rom on each profile, and also checks the oracle against that load on the CGB side. */

#define KIB ((size_t)1024u)
#define MIB (KIB * KIB)
#define MAX_IMAGE (8u * MIB + 1u)
#define SENTINEL 0xA7u

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

/* PGB: bit 7 set and bit 2 or bit 3 set (D-03). */
static int is_pgb(uint8_t flag) { return (flag & 0x80u) != 0u && (flag & 0x0Cu) != 0u; }

/* skew != 0 moves the PGB check ahead of the checksum check: the deliberately wrong validator
 * the parity loop must be able to catch. */
static gbb_error expected_result(gbb_profile profile, uint8_t type, uint8_t rom_code,
                                 uint8_t ram_code, size_t length, int checksum_ok,
                                 uint8_t cgb_flag, int skew) {
    const int reject_pgb = profile == GBB_PROFILE_CGB_CPU_E && is_pgb(cgb_flag);
    if (length > 8u * MIB) return GBB_ROM_TOO_LARGE;
    const family_row *row = find_row(type);
    if (row == NULL) return length > 2u * MIB ? GBB_ROM_TOO_LARGE : GBB_UNSUPPORTED_CARTRIDGE;
    if (length > row->ceiling) return GBB_ROM_TOO_LARGE;
    if (rom_code > row->max_rom_code) return GBB_UNSUPPORTED_ROM_SIZE;
    if (!ram_ok(row, rom_code, ram_code)) return GBB_UNSUPPORTED_RAM_SIZE;
    const size_t declared = (32u * KIB) << rom_code;
    if (length < declared) return GBB_ROM_TRUNCATED;
    if (length > declared) return GBB_ROM_SIZE_MISMATCH;
    if (skew && reject_pgb) return GBB_UNSUPPORTED_EXECUTION_MODE;
    if (!checksum_ok) return GBB_INVALID_ROM;
    if (row->is_mbc3 && (rom_code == 7u || (row->ram == RAM_MBC3 && ram_code == 5u)))
        return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
    if (reject_pgb) return GBB_UNSUPPORTED_EXECUTION_MODE;
    return GBB_OK;
}

static gbb_exec_mode expected_mode(gbb_profile profile, uint8_t cgb_flag) {
    if (profile == GBB_PROFILE_DMG_CPU_B) return GBB_MODE_DMG;
    return (cgb_flag & 0x80u) != 0u ? GBB_MODE_CGB : GBB_MODE_CGB_DMG_COMPAT;
}

/* D-03 table as literals. */
typedef struct { uint8_t flag; gbb_cgb_support support; } support_row;
static const support_row support_rows[] = {
    {0x00u, GBB_CGB_SUPPORT_NONE},     {0x80u, GBB_CGB_SUPPORT_ENHANCED},
    {0xC0u, GBB_CGB_SUPPORT_ONLY},     {0x81u, GBB_CGB_SUPPORT_OTHER},
    {0x84u, GBB_CGB_SUPPORT_PGB},      {0x88u, GBB_CGB_SUPPORT_PGB},
    {0xFFu, GBB_CGB_SUPPORT_PGB},
};
#define SUPPORT_ROWS (sizeof(support_rows) / sizeof(support_rows[0]))

/* ---- ROM builders -------------------------------------------------------- */

static uint8_t *image;

static void set_header(uint8_t type, uint8_t rom_code, uint8_t ram_code, int checksum_ok,
                       uint8_t cgb_flag) {
    memset(image + 0x100u, 0, 0x50u);
    image[0x143u] = cgb_flag;
    image[0x147u] = type;
    image[0x148u] = rom_code;
    image[0x149u] = ram_code;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - image[i] - 1u);
    image[0x14Du] = checksum_ok ? checksum : (uint8_t)(checksum ^ 0x5Au);
}

/* A valid 32 KiB image with the given type, RAM code and $143. */
static size_t small_rom(uint8_t type, uint8_t ram_code, uint8_t cgb_flag) {
    set_header(type, 0u, ram_code, 1, cgb_flag);
    return 32u * KIB;
}

static void fill_info(gbb_info *info, uint32_t size) {
    memset(info, SENTINEL, sizeof(*info));
    info->struct_size = size;
}

static int info_untouched(const gbb_info *info, uint32_t size) {
    gbb_info want;
    fill_info(&want, size);
    return memcmp(info, &want, sizeof(want)) == 0;
}

static gbb_instance *new_instance(void) {
    gbb_instance *m = NULL;
    return gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK ? m : NULL;
}

static gbb_instance *new_cgb_instance(void) {
    gbb_instance *m = NULL;
    return gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK ? m : NULL;
}

/* ---- cases --------------------------------------------------------------- */

static int probe_tracer(void) {
    const size_t len = small_rom(0x00u, 0u, 0x80u);
    gbb_info info;
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, &info) == GBB_OK);
    REQUIRE(info.mode == GBB_MODE_DMG);
    REQUIRE(info.cgb_support == GBB_CGB_SUPPORT_ENHANCED);
    REQUIRE(info.profile == GBB_PROFILE_DMG_CPU_B);
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, len, &info) == GBB_OK);
    REQUIRE(info.mode == GBB_MODE_CGB);
    REQUIRE(info.profile == GBB_PROFILE_CGB_CPU_E);
    return 0;
}

static int info_no_rom(void) {
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    gbb_info info;
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &info) == GBB_OK);
    REQUIRE(info.struct_size == GBB_INFO_SIZE_V1);
    REQUIRE(info.profile == GBB_PROFILE_DMG_CPU_B);
    REQUIRE(info.mode == GBB_MODE_NONE);
    REQUIRE(info.flags == 0u);
    REQUIRE(info.cgb_flag == 0u && info.cgb_support == 0u && info.cartridge_type == 0u);
    REQUIRE(info.reserved0 == 0u && info.rom_size_bytes == 0u && info.ram_size_bytes == 0u);
    gbb_destroy(m);
    return 0;
}

typedef struct {
    uint8_t type, ram_code;
    uint32_t flags, ram_bytes;
} info_row;

static int info_after_load(void) {
    static const info_row table[] = {
        /* MBC3 $10 carries the timer; $13 is battery RAM without one; $0F is timer without RAM. */
        {0x10u, 0x03u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_BATTERY | GBB_INFO_HAS_RTC, 32768u},
        {0x13u, 0x03u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_BATTERY, 32768u},
        {0x0Fu, 0x00u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_BATTERY | GBB_INFO_HAS_RTC, 0u},
        {0x06u, 0x00u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_BATTERY, 512u},
        {0x05u, 0x00u, GBB_INFO_HAS_ROM, 512u},
        {0x1Eu, 0x03u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_BATTERY | GBB_INFO_HAS_RUMBLE, 32768u},
        {0x1Cu, 0x00u, GBB_INFO_HAS_ROM | GBB_INFO_HAS_RUMBLE, 0u},
        {0x12u, 0x02u, GBB_INFO_HAS_ROM, 8192u},
        {0x00u, 0x00u, GBB_INFO_HAS_ROM, 0u},
    };
    for (size_t i = 0u; i < sizeof(table) / sizeof(table[0]); ++i) {
        const size_t len = small_rom(table[i].type, table[i].ram_code, 0x00u);
        gbb_instance *m = new_instance();
        REQUIRE(m != NULL);
        REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
        gbb_info info, probed;
        fill_info(&info, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_get_info(m, &info) == GBB_OK);
        REQUIRE(info.mode == GBB_MODE_DMG);
        if (info.flags != table[i].flags)
            fprintf(stderr, "type=%02X flags=%02X want=%02X\n", table[i].type, info.flags,
                    table[i].flags);
        REQUIRE(info.flags == table[i].flags);
        REQUIRE(info.ram_size_bytes == table[i].ram_bytes);
        REQUIRE(info.rom_size_bytes == len);
        REQUIRE(info.cartridge_type == table[i].type);
        REQUIRE(info.cgb_flag == 0u && info.cgb_support == GBB_CGB_SUPPORT_NONE);
        /* Instance and probe describe one ROM identically. */
        fill_info(&probed, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, &probed) == GBB_OK);
        REQUIRE(memcmp(&info, &probed, sizeof(info)) == 0);
        gbb_destroy(m);
    }
    return 0;
}

static int info_reset_constant(void) {
    const size_t len = small_rom(0x13u, 0x03u, 0xC0u);
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
    gbb_info before, after;
    fill_info(&before, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &before) == GBB_OK);
    REQUIRE(before.flags & GBB_INFO_CGB_ONLY_ON_DMG);
    (void)gbb_run(m, 20000u, NULL, 0u);
    REQUIRE(gbb_reset(m) == GBB_OK);
    fill_info(&after, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &after) == GBB_OK);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    gbb_destroy(m);
    return 0;
}

static int info_failed_load_unchanged(void) {
    size_t len = small_rom(0x01u, 0u, 0x80u);
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
    gbb_info before, after;
    fill_info(&before, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &before) == GBB_OK);
    /* Truncated, bad checksum, and an unsupported type each fail with a different $143. */
    REQUIRE(gbb_load_rom(m, image, 0x100u) == GBB_ROM_TRUNCATED);
    set_header(0x01u, 0u, 0u, 0, 0xC0u);
    REQUIRE(gbb_load_rom(m, image, 32u * KIB) == GBB_INVALID_ROM);
    set_header(0x20u, 0u, 0u, 1, 0xC0u);
    REQUIRE(gbb_load_rom(m, image, 32u * KIB) == GBB_UNSUPPORTED_CARTRIDGE);
    fill_info(&after, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &after) == GBB_OK);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    gbb_destroy(m);
    return 0;
}

typedef struct {
    gbb_info info;
    uint8_t extra[12];
} big_info;

static int info_struct_size_for(int use_probe) {
    const size_t len = small_rom(0x00u, 0u, 0x80u);
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
#define CALL(buf) (use_probe ? gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, (buf)) \
                             : gbb_get_info(m, (buf)))
    static const uint32_t too_small[] = {0u, 1u, 27u};
    for (size_t i = 0u; i < sizeof(too_small) / sizeof(too_small[0]); ++i) {
        gbb_info info;
        fill_info(&info, too_small[i]);
        REQUIRE(CALL(&info) == GBB_INVALID_ARGUMENT);
        REQUIRE(info_untouched(&info, too_small[i]));
    }
    gbb_info exact;
    fill_info(&exact, GBB_INFO_SIZE_V1);
    REQUIRE(CALL(&exact) == GBB_OK);
    REQUIRE(exact.struct_size == GBB_INFO_SIZE_V1);
    REQUIRE(exact.mode == GBB_MODE_DMG && exact.cgb_support == GBB_CGB_SUPPORT_ENHANCED);
    big_info big;
    memset(&big, SENTINEL, sizeof(big));
    REQUIRE(sizeof(big) == 40u);
    big.info.struct_size = (uint32_t)sizeof(big);
    REQUIRE(CALL(&big.info) == GBB_OK);
    REQUIRE(big.info.struct_size == GBB_INFO_SIZE_V1);
    for (size_t i = 0u; i < sizeof(big.extra); ++i) REQUIRE(big.extra[i] == SENTINEL);
    REQUIRE(memcmp(&big.info, &exact, sizeof(exact)) == 0);
#undef CALL
    gbb_destroy(m);
    return 0;
}

static int info_struct_size(void) {
    REQUIRE(info_struct_size_for(1) == 0);
    REQUIRE(info_struct_size_for(0) == 0);
    return 0;
}

static int cgb_only_on_dmg(void) {
    gbb_info info;
    size_t len = small_rom(0x00u, 0u, 0xC0u);
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &info) == GBB_OK);
    REQUIRE((info.flags & GBB_INFO_CGB_ONLY_ON_DMG) != 0u);
    REQUIRE(info.cgb_support == GBB_CGB_SUPPORT_ONLY && info.mode == GBB_MODE_DMG);
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, &info) == GBB_OK);
    REQUIRE((info.flags & GBB_INFO_CGB_ONLY_ON_DMG) != 0u);
    /* On the CGB profile the same ROM is a native CGB ROM, so there is nothing to flag. */
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, len, &info) == GBB_OK);
    REQUIRE((info.flags & GBB_INFO_CGB_ONLY_ON_DMG) == 0u && info.mode == GBB_MODE_CGB);
    /* $80 and $00 never set the flag on the DMG profile. */
    static const uint8_t others[] = {0x00u, 0x80u, 0x81u, 0x84u};
    for (size_t i = 0u; i < sizeof(others); ++i) {
        len = small_rom(0x00u, 0u, others[i]);
        fill_info(&info, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, &info) == GBB_OK);
        REQUIRE((info.flags & GBB_INFO_CGB_ONLY_ON_DMG) == 0u);
        REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
        fill_info(&info, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_get_info(m, &info) == GBB_OK);
        REQUIRE((info.flags & GBB_INFO_CGB_ONLY_ON_DMG) == 0u);
    }
    gbb_destroy(m);
    return 0;
}

static int probe_matrix(void) {
    for (int p = 0; p < 2; ++p) {
        const gbb_profile profile = p == 0 ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E;
        for (size_t i = 0u; i < SUPPORT_ROWS; ++i) {
            const uint8_t flag = support_rows[i].flag;
            const size_t len = small_rom(0x00u, 0u, flag);
            gbb_info info;
            fill_info(&info, GBB_INFO_SIZE_V1);
            const gbb_error got = gbb_probe_rom(profile, image, len, &info);
            const gbb_error want = expected_result(profile, 0x00u, 0u, 0u, len, 1, flag, 0);
            if (got != want) {
                fprintf(stderr, "profile=%d flag=%02X want=%d got=%d\n", (int)profile, flag,
                        (int)want, (int)got);
                return 1;
            }
            if (want != GBB_OK) {
                REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
                continue;
            }
            REQUIRE(info.mode == (uint32_t)expected_mode(profile, flag));
            REQUIRE(info.cgb_support == (uint8_t)support_rows[i].support);
            REQUIRE(info.cgb_flag == flag);
        }
    }
    /* The headline rows, asserted directly so a mirrored oracle bug cannot hide. */
    gbb_info info;
    size_t len = small_rom(0x00u, 0u, 0x84u);
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, len, &info) ==
            GBB_UNSUPPORTED_EXECUTION_MODE);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_DMG_CPU_B, image, len, &info) == GBB_OK);
    REQUIRE(info.cgb_support == GBB_CGB_SUPPORT_PGB && info.mode == GBB_MODE_DMG);
    len = small_rom(0x00u, 0u, 0x00u);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, len, &info) == GBB_OK);
    REQUIRE(info.mode == GBB_MODE_CGB_DMG_COMPAT);
    return 0;
}

static int probe_pgb(void) {
    gbb_info info;
    /* Existing errors keep precedence over the PGB rejection. */
    set_header(0x00u, 0u, 0u, 0, 0x84u);
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 32u * KIB, &info) == GBB_INVALID_ROM);
    REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
    set_header(0x00u, 0u, 0u, 1, 0x88u);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 32u * KIB - 1u, &info) ==
            GBB_ROM_TRUNCATED);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 0x100u, &info) == GBB_ROM_TRUNCATED);
    set_header(0x20u, 0u, 0u, 1, 0xFFu);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 32u * KIB, &info) ==
            GBB_UNSUPPORTED_CARTRIDGE);
    set_header(0x10u, 7u, 3u, 1, 0x84u);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 4u * MIB, &info) ==
            GBB_UNSUPPORTED_CARTRIDGE_VARIANT);
    REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
    /* A clean PGB image reaches the rejection. */
    set_header(0x00u, 0u, 0u, 1, 0x84u);
    REQUIRE(gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, 32u * KIB, &info) ==
            GBB_UNSUPPORTED_EXECUTION_MODE);
    REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
    /* The DMG profile ignores $143: the same image loads. */
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_load_rom(m, image, 32u * KIB) == GBB_OK);
    gbb_destroy(m);
    return 0;
}

static const uint8_t rom_codes[] = {0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 0x09u, 0x52u, 0x53u,
                                    0x54u, 0xFFu};
static const uint8_t ram_codes[] = {0u, 1u, 2u, 3u, 4u, 5u, 6u, 0xFFu};
static const uint8_t parity_types[] = {0x00u, 0x01u, 0x02u, 0x03u, 0x04u, 0x05u, 0x06u, 0x07u,
                                       0x0Fu, 0x10u, 0x11u, 0x12u, 0x13u, 0x19u, 0x1Au, 0x1Bu,
                                       0x1Cu, 0x1Du, 0x1Eu, 0x1Fu, 0x20u, 0xFCu, 0xFFu};

/* Exhaustively compare probe and real-loader results across both profiles and the header matrix.
 * The independent CGB oracle remains a third check; *runs counts every matrix entry. */
static unsigned long parity_sweep(gbb_instance *scratch_dmg, gbb_instance *scratch_cgb,
                                  unsigned long *runs) {
    unsigned long mismatches = 0u;
    for (int p = 0; p < 2; ++p) {
        const gbb_profile profile = p == 0 ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E;
        for (size_t t = 0u; t < sizeof(parity_types); ++t)
            for (size_t r = 0u; r < sizeof(rom_codes); ++r)
                for (size_t m = 0u; m < sizeof(ram_codes); ++m) {
                    const size_t base = declared_length(rom_codes[r]);
                    const size_t lengths[3] = {base, base - 1u, base + 1u};
                    for (int l = 0; l < 3; ++l)
                        for (int ck = 0; ck < 2; ++ck)
                            for (size_t f = 0u; f < SUPPORT_ROWS; ++f) {
                                const uint8_t flag = support_rows[f].flag;
                                set_header(parity_types[t], rom_codes[r], ram_codes[m], ck, flag);
                                gbb_info info;
                                fill_info(&info, GBB_INFO_SIZE_V1);
                                const gbb_error probe =
                                    gbb_probe_rom(profile, image, lengths[l], &info);
                                const gbb_error ref = gbb_load_rom(
                                    profile == GBB_PROFILE_DMG_CPU_B ? scratch_dmg : scratch_cgb,
                                    image, lengths[l]);
                                if (profile == GBB_PROFILE_CGB_CPU_E &&
                                    ref != expected_result(profile, parity_types[t], rom_codes[r],
                                                           ram_codes[m], lengths[l], ck, flag, 0)) {
                                    ++mismatches;
                                    fprintf(stderr, "oracle: type=%02X rom=%02X ram=%02X "
                                            "len=%zu ck=%d flag=%02X load=%d\n",
                                            parity_types[t], rom_codes[r], ram_codes[m],
                                            lengths[l], ck, flag, (int)ref);
                                }
                                ++*runs;
                                if (probe != ref) {
                                    ++mismatches;
                                    fprintf(stderr,
                                            "parity: profile=%d type=%02X rom=%02X ram=%02X "
                                            "len=%zu ck=%d flag=%02X probe=%d ref=%d\n",
                                            (int)profile, parity_types[t], rom_codes[r],
                                            ram_codes[m], lengths[l], ck, flag, (int)probe,
                                            (int)ref);
                                }
                                if (probe != GBB_OK &&
                                    !info_untouched(&info, GBB_INFO_SIZE_V1))
                                    ++mismatches;
                            }
                }
    }
    return mismatches;
}

static int probe_parity(void) {
    gbb_instance *scratch = new_instance();
    gbb_instance *scratch_cgb = new_cgb_instance();
    REQUIRE(scratch != NULL && scratch_cgb != NULL);
    unsigned long runs = 0u;
    REQUIRE(parity_sweep(scratch, scratch_cgb, &runs) == 0u);
    REQUIRE(runs > 100000u);
    /* Negative control: PGB-before-checksum changes this valid PGB header with a bad checksum. */
    set_header(0x00u, 0u, 0u, 0, 0x84u);
    const size_t len = 32u * KIB;
    gbb_info info;
    fill_info(&info, GBB_INFO_SIZE_V1);
    const gbb_error probe = gbb_probe_rom(GBB_PROFILE_CGB_CPU_E, image, len, &info);
    const gbb_error load = gbb_load_rom(scratch_cgb, image, len);
    const gbb_error skewed = expected_result(GBB_PROFILE_CGB_CPU_E, 0x00u, 0u, 0u,
                                             len, 0, 0x84u, 1);
    REQUIRE(probe == GBB_INVALID_ROM);
    REQUIRE(load == probe);
    REQUIRE(skewed == GBB_UNSUPPORTED_EXECUTION_MODE);
    REQUIRE(skewed != probe);
    REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
    gbb_destroy(scratch);
    gbb_destroy(scratch_cgb);
    return 0;
}

static int profile_unknown(void) {
    static const uint32_t bad[] = {0u, 3u, 255u};
    const size_t len = small_rom(0x00u, 0u, 0x00u);
    for (size_t i = 0u; i < sizeof(bad) / sizeof(bad[0]); ++i) {
        gbb_info info;
        fill_info(&info, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_probe_rom((gbb_profile)bad[i], image, len, &info) == GBB_UNSUPPORTED_PROFILE);
        REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
        /* The unknown profile outranks every argument error. */
        REQUIRE(gbb_probe_rom((gbb_profile)bad[i], image, len, NULL) == GBB_UNSUPPORTED_PROFILE);
        REQUIRE(gbb_probe_rom((gbb_profile)bad[i], NULL, 1u, &info) == GBB_UNSUPPORTED_PROFILE);
        fill_info(&info, 0u);
        REQUIRE(gbb_probe_rom((gbb_profile)bad[i], image, len, &info) == GBB_UNSUPPORTED_PROFILE);
        gbb_instance *m = (gbb_instance *)(void *)&info;
        REQUIRE(gbb_create((gbb_profile)bad[i], &m) == GBB_UNSUPPORTED_PROFILE);
        REQUIRE(m == NULL);
    }
    return 0;
}

/* D-01: the create switch accepts exactly the two implemented profiles. */
static int profile_create(void) {
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(m != NULL);
    gbb_info info;
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(m, &info) == GBB_OK);
    REQUIRE(info.profile == GBB_PROFILE_CGB_CPU_E && info.mode == GBB_MODE_NONE);
    gbb_destroy(m);
    static const uint32_t bad[] = {0u, 3u, 255u};
    for (size_t i = 0u; i < sizeof(bad) / sizeof(bad[0]); ++i) {
        m = NULL;
        REQUIRE(gbb_create((gbb_profile)bad[i], &m) == GBB_UNSUPPORTED_PROFILE);
        REQUIRE(m == NULL);
    }
    return 0;
}

/* D-05: no colour output yet, so a valid copy on the CGB profile is unsupported while argument
 * errors keep their code and the DMG profile is unchanged. */
static int copy_frame_cgb(void) {
    const size_t len = small_rom(0x00u, 0u, 0x80u);
    static uint8_t pixels[160u * 144u];
    gbb_frame_info finfo;
    for (int p = 0; p < 2; ++p) {
        gbb_instance *m = p == 0 ? new_instance() : new_cgb_instance();
        REQUIRE(m != NULL);
        REQUIRE(gbb_load_rom(m, image, len) == GBB_OK);
        memset(pixels, SENTINEL, sizeof(pixels));
        memset(&finfo, SENTINEL, sizeof(finfo));
        REQUIRE(gbb_copy_frame(m, NULL, sizeof(pixels), 160u, &finfo) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_copy_frame(m, pixels, sizeof(pixels), 160u, NULL) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_copy_frame(m, pixels, sizeof(pixels), 159u, &finfo) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_copy_frame(m, pixels, 100u, 160u, &finfo) == GBB_INVALID_ARGUMENT);
        const gbb_error before = gbb_copy_frame(m, pixels, sizeof(pixels), 160u, &finfo);
        if (p == 0) {
            /* DMG: a fresh frame is not ready, exactly as before this plan. */
            REQUIRE(before == GBB_FRAME_NOT_READY);
        } else {
            REQUIRE(before == GBB_UNSUPPORTED_PROFILE);
        }
        for (size_t i = 0u; i < sizeof(pixels); ++i) REQUIRE(pixels[i] == SENTINEL);
        (void)gbb_run(m, 4u * 70224u * 2u, NULL, 0u);
        const gbb_error after = gbb_copy_frame(m, pixels, sizeof(pixels), 160u, &finfo);
        if (p == 0) REQUIRE(after == GBB_OK && finfo.width == 160u && finfo.height == 144u);
        else REQUIRE(after == GBB_UNSUPPORTED_PROFILE);
        gbb_destroy(m);
    }
    return 0;
}

static int probe_args(void) {
    const size_t len = small_rom(0x00u, 0u, 0x00u);
    static const gbb_profile profiles[] = {GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_CGB_CPU_E};
    for (size_t p = 0u; p < 2u; ++p) {
        gbb_info info;
        REQUIRE(gbb_probe_rom(profiles[p], image, len, NULL) == GBB_INVALID_ARGUMENT);
        fill_info(&info, GBB_INFO_SIZE_V1);
        REQUIRE(gbb_probe_rom(profiles[p], NULL, 1u, &info) == GBB_INVALID_ARGUMENT);
        REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
        REQUIRE(gbb_probe_rom(profiles[p], NULL, 0u, &info) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_probe_rom(profiles[p], image, 0u, &info) == GBB_INVALID_ARGUMENT);
        REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
        for (uint32_t size = 0u; size < GBB_INFO_SIZE_V1; size += 9u) {
            fill_info(&info, size);
            REQUIRE(gbb_probe_rom(profiles[p], image, len, &info) == GBB_INVALID_ARGUMENT);
            REQUIRE(info_untouched(&info, size));
        }
    }
    gbb_info info;
    fill_info(&info, GBB_INFO_SIZE_V1);
    REQUIRE(gbb_get_info(NULL, &info) == GBB_INVALID_ARGUMENT);
    gbb_instance *m = new_instance();
    REQUIRE(m != NULL);
    REQUIRE(gbb_get_info(m, NULL) == GBB_INVALID_ARGUMENT);
    REQUIRE(info_untouched(&info, GBB_INFO_SIZE_V1));
    gbb_destroy(m);
    return 0;
}

typedef struct { const char *name; int (*run)(void); } test_case;

static const test_case cases[] = {
    {"probe_tracer", probe_tracer},
    {"info_no_rom", info_no_rom},
    {"info_after_load", info_after_load},
    {"info_reset_constant", info_reset_constant},
    {"info_failed_load_unchanged", info_failed_load_unchanged},
    {"info_struct_size", info_struct_size},
    {"cgb_only_on_dmg", cgb_only_on_dmg},
    {"probe_matrix", probe_matrix},
    {"probe_pgb", probe_pgb},
    {"probe_parity", probe_parity},
    {"profile_unknown", profile_unknown},
    {"profile_create", profile_create},
    {"copy_frame_cgb", copy_frame_cgb},
    {"probe_args", probe_args},
};

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_cgb_profile <case>\n");
        return 2;
    }
    image = calloc(1u, MAX_IMAGE);
    if (image == NULL) return 2;
    int rc = 2;
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i)
        if (strcmp(argv[1], cases[i].name) == 0) {
            rc = cases[i].run();
            if (rc == 0) printf("ok 1 - cgb_%s\n", cases[i].name);
            break;
        }
    if (rc == 2) fprintf(stderr, "unknown case %s\n", argv[1]);
    free(image);
    return rc;
}
