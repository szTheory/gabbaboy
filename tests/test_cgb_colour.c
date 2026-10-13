/* Public-API colour cases (Phase 11). Links GabbaBoy::core only; no core internals.
 *
 * Usage: test_cgb_colour <case> */
#include "gabbaboy/gabbaboy.h"

#include <stdalign.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

#define ROM_SIZE 32768u
#define FRAME_HALF_DOTS 140448u
#define FRAME_W 160u
#define FRAME_H 144u

static void make_rom(uint8_t *rom, uint8_t cgb_flag) {
    memset(rom, 0, ROM_SIZE);
    rom[0x143u] = cgb_flag;
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

/* D-16: gbb_copy_frame stays unsupported on the CGB profile (the DMG shade buffer is not a
 * colour frame) in both CGB mode and compatibility mode, with the caller buffer untouched. */
static int check_copy(gbb_profile profile, uint8_t cgb_flag, gbb_error expected) {
    static uint8_t rom[ROM_SIZE];
    static uint8_t pixels[FRAME_W * FRAME_H];
    gbb_frame_info info;
    gbb_instance *m = NULL;
    make_rom(rom, cgb_flag);
    memset(pixels, 0xA7, sizeof(pixels));
    REQUIRE(gbb_create(profile, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    for (int i = 0; i < 2; ++i) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        REQUIRE(r.reason != GBB_STOP_INVALID_STATE);
    }
    REQUIRE(gbb_copy_frame(m, pixels, sizeof(pixels), FRAME_W, &info) == expected);
    if (expected == GBB_UNSUPPORTED_PROFILE) {
        for (size_t i = 0; i < sizeof(pixels); ++i) REQUIRE(pixels[i] == 0xA7u);
    }
    gbb_destroy(m);
    return 0;
}

static int cgb_colour_copy_frame_unsupported(void) {
    if (check_copy(GBB_PROFILE_CGB_CPU_E, 0x80u, GBB_UNSUPPORTED_PROFILE) != 0) return 1;
    if (check_copy(GBB_PROFILE_CGB_CPU_E, 0x00u, GBB_UNSUPPORTED_PROFILE) != 0) return 1;
    if (check_copy(GBB_PROFILE_DMG_CPU_B, 0x00u, GBB_OK) != 0) return 1;
    return 0;
}

/* ---- gbb_copy_frame_rgb555 (D-15) ---- */
#define RGB_BUF_VALUES 30000u
static alignas(8) uint16_t rgb_buf[RGB_BUF_VALUES];

static gbb_instance *rgb_instance(gbb_profile profile, uint8_t cgb_flag, int frames) {
    static uint8_t rom[ROM_SIZE];
    gbb_instance *m = NULL;
    make_rom(rom, cgb_flag);
    if (gbb_create(profile, &m) != GBB_OK) return NULL;
    if (gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) { gbb_destroy(m); return NULL; }
    for (int i = 0; i < frames; ++i) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        if (r.reason == GBB_STOP_INVALID_STATE) { gbb_destroy(m); return NULL; }
    }
    return m;
}

static int info_is_sentinel(const gbb_frame_info *info) {
    const uint8_t *b = (const uint8_t *)info;
    for (size_t i = 0; i < sizeof(*info); ++i) if (b[i] != 0x5Au) return 0;
    return 1;
}

static int buf_is_sentinel(size_t bytes) {
    const uint8_t *b = (const uint8_t *)rgb_buf;
    for (size_t i = 0; i < bytes; ++i) if (b[i] != 0xA7u) return 0;
    return 1;
}

/* One rejected call: the error must match and neither output may change. */
static int rgb_reject(const gbb_instance *m, size_t pixel_offset_bytes, int null_pixels,
                      size_t capacity, size_t pitch, int null_info, gbb_error expected) {
    gbb_frame_info info;
    memset(rgb_buf, 0xA7, sizeof(rgb_buf));
    memset(&info, 0x5A, sizeof(info));
    uint16_t *px = null_pixels ? NULL : (uint16_t *)((uint8_t *)rgb_buf + pixel_offset_bytes);
    gbb_error e = gbb_copy_frame_rgb555(m, px, capacity, pitch, null_info ? NULL : &info);
    REQUIRE(e == expected);
    REQUIRE(buf_is_sentinel(sizeof(rgb_buf)));
    REQUIRE(info_is_sentinel(&info));
    return 0;
}

static int cgb_rgb555_args(void) {
    gbb_instance *m = rgb_instance(GBB_PROFILE_CGB_CPU_E, 0x80u, 2);
    gbb_instance *dmg = rgb_instance(GBB_PROFILE_DMG_CPU_B, 0x00u, 2);
    REQUIRE(m != NULL && dmg != NULL);
    const size_t ok_cap = 143u * 320u + 320u;
    const gbb_error bad = GBB_INVALID_ARGUMENT;
    REQUIRE(rgb_reject(NULL, 0, 0, ok_cap, 320u, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 1, ok_cap, 320u, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, 320u, 1, bad) == 0);
    REQUIRE(rgb_reject(m, 1, 0, ok_cap, 320u, 0, bad) == 0);   /* misaligned pointer */
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, 321u, 0, bad) == 0);   /* odd pitch */
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, 318u, 0, bad) == 0);   /* below one row */
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, 0u, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, SIZE_MAX, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 0, ok_cap, SIZE_MAX - 1u, 0, bad) == 0); /* even, overflows */
    REQUIRE(rgb_reject(m, 0, 0, ok_cap - 1u, 320u, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 0, 0u, 320u, 0, bad) == 0);
    REQUIRE(rgb_reject(m, 0, 0, SIZE_MAX, SIZE_MAX, 0, bad) == 0);
    /* a DMG instance with bad arguments still reports the argument error, not the profile */
    REQUIRE(rgb_reject(dmg, 0, 1, ok_cap, 320u, 0, bad) == 0);
    REQUIRE(rgb_reject(dmg, 0, 0, ok_cap, 321u, 0, bad) == 0);
    /* out_info inside the pixel range */
    memset(rgb_buf, 0xA7, sizeof(rgb_buf));
    REQUIRE(gbb_copy_frame_rgb555(m, rgb_buf, ok_cap, 320u, (gbb_frame_info *)(rgb_buf + 8)) == bad);
    REQUIRE(buf_is_sentinel(sizeof(rgb_buf)));
    /* the valid call right at the bound succeeds */
    gbb_frame_info info;
    REQUIRE(gbb_copy_frame_rgb555(m, rgb_buf, ok_cap, 320u, &info) == GBB_OK);
    gbb_destroy(m);
    gbb_destroy(dmg);
    return 0;
}

static int cgb_rgb555_dmg_profile(void) {
    gbb_instance *dmg = rgb_instance(GBB_PROFILE_DMG_CPU_B, 0x00u, 2);
    REQUIRE(dmg != NULL);
    REQUIRE(rgb_reject(dmg, 0, 0, 143u * 320u + 320u, 320u, 0, GBB_UNSUPPORTED_PROFILE) == 0);
    gbb_destroy(dmg);
    return 0;
}

static int cgb_rgb555_not_ready(void) {
    gbb_frame_info info;
    gbb_instance *m = rgb_instance(GBB_PROFILE_CGB_CPU_E, 0x80u, 0);
    REQUIRE(m != NULL);
    REQUIRE(rgb_reject(m, 0, 0, 143u * 320u + 320u, 320u, 0, GBB_FRAME_NOT_READY) == 0);
    for (int i = 0; i < 2; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, rgb_buf, 143u * 320u + 320u, 320u, &info) == GBB_OK);
    REQUIRE(gbb_reset(m) == GBB_OK);
    REQUIRE(rgb_reject(m, 0, 0, 143u * 320u + 320u, 320u, 0, GBB_FRAME_NOT_READY) == 0);
    gbb_destroy(m);
    return 0;
}

static int cgb_rgb555_both_modes(void) {
    const uint8_t flags[2] = {0x80u, 0x00u};
    for (int k = 0; k < 2; ++k) {
        gbb_instance *m = rgb_instance(GBB_PROFILE_CGB_CPU_E, flags[k], 2);
        gbb_frame_info info;
        const size_t pitch = 400u;
        const size_t cap = 143u * pitch + 320u;
        REQUIRE(m != NULL);
        memset(rgb_buf, 0xA7, sizeof(rgb_buf));
        memset(&info, 0, sizeof(info));
        REQUIRE(gbb_copy_frame_rgb555(m, rgb_buf, cap, pitch, &info) == GBB_OK);
        REQUIRE(info.width == FRAME_W && info.height == FRAME_H && info.generation >= 1u);
        const uint8_t *bytes = (const uint8_t *)rgb_buf;
        for (size_t y = 0; y < FRAME_H; ++y) {
            const uint16_t *row = (const uint16_t *)(bytes + y * pitch);
            for (size_t x = 0; x < FRAME_W; ++x) REQUIRE(row[x] <= 0x7FFFu);
            if (y + 1u < FRAME_H)
                for (size_t b = 320u; b < pitch; ++b) REQUIRE(bytes[y * pitch + b] == 0xA7u);
        }
        gbb_destroy(m);
    }
    return 0;
}

/* D-02: a guest that turns the LCD off in VBlank leaves the last completed frame readable. */
static int cgb_rgb555_lcd_off(void) {
    static uint8_t rom[ROM_SIZE];
    static const uint8_t code[] = {
        0xF0, 0x44, 0xFE, 0x90, 0x20, 0xFA,  /* wait for LY == 144 */
        0xAF, 0xE0, 0x40,                    /* LCDC = 0: LCD off */
        0x18, 0xFE                           /* spin */
    };
    static uint16_t first[FRAME_W * FRAME_H], later[FRAME_W * FRAME_H];
    gbb_frame_info a, b;
    gbb_instance *m = NULL;
    make_rom(rom, 0x80u);
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;
    memcpy(rom + 0x150u, code, sizeof(code));
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    for (int i = 0; i < 2; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, first, sizeof(first), 320u, &a) == GBB_OK);
    for (int i = 0; i < 5; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, later, sizeof(later), 320u, &b) == GBB_OK);
    REQUIRE(a.generation >= 1u && b.generation == a.generation);
    REQUIRE(memcmp(first, later, sizeof(first)) == 0);
    gbb_destroy(m);
    return 0;
}

typedef int (*case_fn)(void);
static const struct { const char *name; case_fn fn; } cases[] = {
    {"cgb_colour_copy_frame_unsupported", cgb_colour_copy_frame_unsupported},
    {"cgb_rgb555_args", cgb_rgb555_args},
    {"cgb_rgb555_dmg_profile", cgb_rgb555_dmg_profile},
    {"cgb_rgb555_not_ready", cgb_rgb555_not_ready},
    {"cgb_rgb555_both_modes", cgb_rgb555_both_modes},
    {"cgb_rgb555_lcd_off", cgb_rgb555_lcd_off},
};

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        int rc = cases[i].fn();
        if (rc == 0) printf("ok 1 - %s\n", cases[i].name);
        return rc;
    }
    return 2;
}
