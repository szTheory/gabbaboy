/* Public-API colour cases (Phase 11). Links GabbaBoy::core only; no core internals.
 *
 * Usage: test_cgb_colour <case> [fixture-dir] */
#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

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

/* ---- compat palette API (D-17, D-17a) ---- */
static const uint16_t default_ramp[4] = {0x639Fu, 0x4275u, 0x254Bu, 0x0421u};

static int palette_is_default(const gbb_compat_palette *p) {
    for (int i = 0; i < 4; ++i)
        if (p->bg[i] != default_ramp[i] || p->obj0[i] != default_ramp[i] ||
            p->obj1[i] != default_ramp[i]) return 0;
    return p->struct_size == GBB_COMPAT_PALETTE_SIZE_V1;
}

static gbb_compat_palette distinct_palette(void) {
    gbb_compat_palette p;
    memset(&p, 0, sizeof(p));
    p.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    for (uint16_t i = 0; i < 4u; ++i) {
        p.bg[i] = (uint16_t)(0x0101u + i);
        p.obj0[i] = (uint16_t)(0x1111u + i);
        p.obj1[i] = (uint16_t)(0x7F00u + i);
    }
    return p;
}

static int palette_equal(const gbb_compat_palette *a, const gbb_compat_palette *b) {
    return memcmp(a->bg, b->bg, sizeof(a->bg)) == 0 && memcmp(a->obj0, b->obj0, sizeof(a->obj0)) == 0 &&
           memcmp(a->obj1, b->obj1, sizeof(a->obj1)) == 0;
}

static int palette_compat_api_default(void) {
    const gbb_profile profiles[2] = {GBB_PROFILE_CGB_CPU_E, GBB_PROFILE_DMG_CPU_B};
    for (int k = 0; k < 2; ++k) {
        gbb_instance *m = NULL;
        gbb_compat_palette got;
        memset(&got, 0x5A, sizeof(got));
        got.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
        REQUIRE(gbb_create(profiles[k], &m) == GBB_OK);
        REQUIRE(gbb_get_compat_palette(m, &got) == GBB_OK);
        REQUIRE(palette_is_default(&got));
        gbb_destroy(m);
    }
    return 0;
}

static int palette_compat_api_roundtrip(void) {
    gbb_instance *m = NULL;
    gbb_compat_palette want = distinct_palette(), got;
    memset(&got, 0, sizeof(got));
    got.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_set_compat_palette(m, &want) == GBB_OK);
    REQUIRE(gbb_get_compat_palette(m, &got) == GBB_OK);
    REQUIRE(palette_equal(&want, &got));
    REQUIRE(gbb_set_compat_palette(m, NULL) == GBB_OK);
    got.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    REQUIRE(gbb_get_compat_palette(m, &got) == GBB_OK);
    REQUIRE(palette_is_default(&got));
    gbb_destroy(m);
    return 0;
}

static int palette_compat_api_get_reject(void) {
    gbb_instance *m = NULL;
    gbb_compat_palette small, before;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    memset(&small, 0x5A, sizeof(small));
    small.struct_size = GBB_COMPAT_PALETTE_SIZE_V1 - 1u;
    before = small;
    REQUIRE(gbb_get_compat_palette(m, &small) == GBB_INVALID_ARGUMENT);
    REQUIRE(memcmp(&small, &before, sizeof(small)) == 0);
    REQUIRE(gbb_get_compat_palette(NULL, &small) == GBB_INVALID_ARGUMENT);
    REQUIRE(memcmp(&small, &before, sizeof(small)) == 0);
    REQUIRE(gbb_get_compat_palette(m, NULL) == GBB_INVALID_ARGUMENT);
    small.struct_size = 0u;
    before = small;
    REQUIRE(gbb_get_compat_palette(m, &small) == GBB_INVALID_ARGUMENT);
    REQUIRE(memcmp(&small, &before, sizeof(small)) == 0);
    gbb_destroy(m);
    return 0;
}

static int palette_compat_api_reject(void) {
    gbb_instance *m = NULL;
    gbb_compat_palette keep = distinct_palette(), bad, got;
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_set_compat_palette(m, &keep) == GBB_OK);
    REQUIRE(gbb_set_compat_palette(NULL, &keep) == GBB_INVALID_ARGUMENT);
    bad = distinct_palette();
    bad.bg[0] = 0x0001u;
    bad.struct_size = GBB_COMPAT_PALETTE_SIZE_V1 - 1u;
    REQUIRE(gbb_set_compat_palette(m, &bad) == GBB_INVALID_ARGUMENT);
    for (int which = 0; which < 3; ++which) {
        for (int i = 0; i < 4; ++i) {
            bad = distinct_palette();
            bad.bg[0] = 0x2222u;   /* a valid first entry that must not leak in */
            uint16_t *arr = which == 0 ? bad.bg : which == 1 ? bad.obj0 : bad.obj1;
            arr[i] = 0x8000u;
            REQUIRE(gbb_set_compat_palette(m, &bad) == GBB_INVALID_ARGUMENT);
        }
    }
    /* eleven valid entries, the last one invalid */
    bad = distinct_palette();
    bad.bg[0] = 0x3333u;
    bad.obj1[3] = 0xFFFFu;
    REQUIRE(gbb_set_compat_palette(m, &bad) == GBB_INVALID_ARGUMENT);
    memset(&got, 0, sizeof(got));
    got.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    REQUIRE(gbb_get_compat_palette(m, &got) == GBB_OK);
    REQUIRE(palette_equal(&keep, &got));
    gbb_destroy(m);
    return 0;
}

static int palette_compat_api_larger(void) {
    gbb_instance *m = NULL;
    struct { gbb_compat_palette p; uint8_t extra[12]; } big;
    gbb_compat_palette want = distinct_palette();
    REQUIRE(sizeof(big) >= 40u);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    memset(&big, 0xEE, sizeof(big));
    memcpy(&big.p, &want, sizeof(want));
    big.p.struct_size = 40u;
    REQUIRE(gbb_set_compat_palette(m, &big.p) == GBB_OK);   /* extra bytes are ignored */
    memset(&big, 0x5A, sizeof(big));
    big.p.struct_size = 40u;
    REQUIRE(gbb_get_compat_palette(m, &big.p) == GBB_OK);
    REQUIRE(big.p.struct_size == GBB_COMPAT_PALETTE_SIZE_V1);
    REQUIRE(palette_equal(&want, &big.p));
    for (size_t i = 0; i < sizeof(big.extra); ++i) REQUIRE(big.extra[i] == 0x5Au);
    gbb_destroy(m);
    return 0;
}

static int palette_compat_api_survives(void) {
    static uint8_t rom[ROM_SIZE];
    gbb_instance *m = rgb_instance(GBB_PROFILE_CGB_CPU_E, 0x00u, 1);
    gbb_compat_palette want = distinct_palette(), got;
    REQUIRE(m != NULL);
    REQUIRE(gbb_set_compat_palette(m, &want) == GBB_OK);
    REQUIRE(gbb_reset(m) == GBB_OK);
    make_rom(rom, 0x80u);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    memset(&got, 0, sizeof(got));
    got.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    REQUIRE(gbb_get_compat_palette(m, &got) == GBB_OK);
    REQUIRE(palette_equal(&want, &got));
    gbb_destroy(m);
    return 0;
}

static int all_pixels_equal(const uint16_t *px, uint16_t value) {
    for (size_t i = 0; i < (size_t)FRAME_W * FRAME_H; ++i) if (px[i] != value) return 0;
    return 1;
}

/* A guest that spins in place, so the screen stays the post-boot blank frame (a zero-filled ROM
 * would slide through the address space and eventually rewrite BGP). */
static gbb_instance *spin_instance(uint8_t cgb_flag, int frames) {
    static uint8_t rom[ROM_SIZE];
    gbb_instance *m = NULL;
    make_rom(rom, cgb_flag);
    rom[0x100u] = 0xC3u; rom[0x101u] = 0x50u; rom[0x102u] = 0x01u;  /* jp $0150 */
    rom[0x150u] = 0x18u; rom[0x151u] = 0xFEu;                        /* jr -2 */
    if (gbb_create(GBB_PROFILE_CGB_CPU_E, &m) != GBB_OK) return NULL;
    if (gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) { gbb_destroy(m); return NULL; }
    for (int i = 0; i < frames; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    return m;
}

static int palette_compat_effect_next_frame(void) {
    static uint16_t a[FRAME_W * FRAME_H], b[FRAME_W * FRAME_H], c[FRAME_W * FRAME_H];
    gbb_frame_info info;
    gbb_compat_palette p = distinct_palette();
    p.bg[0] = 0x1234u;
    gbb_instance *m = spin_instance(0x00u, 2);
    REQUIRE(m != NULL);
    REQUIRE(gbb_copy_frame_rgb555(m, a, sizeof(a), 320u, &info) == GBB_OK);
    REQUIRE(all_pixels_equal(a, 0x639Fu));
    REQUIRE(gbb_set_compat_palette(m, &p) == GBB_OK);
    REQUIRE(gbb_copy_frame_rgb555(m, b, sizeof(b), 320u, &info) == GBB_OK);
    REQUIRE(memcmp(a, b, sizeof(a)) == 0);                  /* completed frame not recoloured */
    for (int i = 0; i < 2; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, c, sizeof(c), 320u, &info) == GBB_OK);
    REQUIRE(all_pixels_equal(c, 0x1234u));
    gbb_destroy(m);

    /* CGB mode colours come from CRAM, so the compat palette changes no pixel. */
    m = spin_instance(0x80u, 2);
    REQUIRE(m != NULL);
    REQUIRE(gbb_copy_frame_rgb555(m, a, sizeof(a), 320u, &info) == GBB_OK);
    REQUIRE(gbb_set_compat_palette(m, &p) == GBB_OK);
    for (int i = 0; i < 2; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, b, sizeof(b), 320u, &info) == GBB_OK);
    REQUIRE(memcmp(a, b, sizeof(a)) == 0);
    gbb_destroy(m);
    return 0;
}

/* ---- Original fixture: colour-hblank.gb (D-23 item 4, D-01) ---- */
static const char *fixture_dir;

static size_t read_fixture(const char *name, uint8_t *buf, size_t capacity) {
    char path[1024];
    if (fixture_dir == NULL || snprintf(path, sizeof(path), "%s/%s", fixture_dir, name) >= (int)sizeof(path))
        return 0;
    FILE *f = fopen(path, "rb");
    if (f == NULL) return 0;
    size_t n = fread(buf, 1, capacity, f);
    int extra = fgetc(f);
    fclose(f);
    return extra == EOF ? n : 0;   /* a ROM larger than the buffer is rejected, not truncated */
}

/* The guest writes BG colour 0 = (y * 229 + 1) & 0x7FFF for row y (manifest protocol). */
static uint16_t hblank_value(size_t y) { return (uint16_t)((y * 229u + 1u) & 0x7FFFu); }

/* Structural predicate first (D-23): every row is uniform and equals its own table value. */
static int hblank_row_matches(const uint16_t *frame, size_t y) {
    const uint16_t *row = frame + y * FRAME_W;
    for (size_t x = 0; x < FRAME_W; ++x) if (row[x] != hblank_value(y)) return 0;
    return 1;
}

#define HBLANK_FRAME_DIGEST "abb528b8ffd636f85dcd62b1f13e60ea2f1ef7ac368c84b4767e5b967d2e9546"

static int cgb_colour_hblank_rows(void) {
    static uint8_t rom[ROM_SIZE];
    static uint16_t frame[FRAME_W * FRAME_H];
    gbb_frame_info info;
    gbb_instance *m = NULL;
    REQUIRE(read_fixture("colour-hblank.gb", rom, sizeof(rom)) == ROM_SIZE);
    REQUIRE(rom[0x143u] == 0x80u);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    /* Pitfall 7: the reset fill (zero) never leaks into a completed frame. No table value is 0. */
    gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    gbb_error first = gbb_copy_frame_rgb555(m, frame, sizeof(frame), 320u, &info);
    if (first == GBB_OK) {
        for (size_t i = 0; i < (size_t)FRAME_W * FRAME_H; ++i) REQUIRE(frame[i] != 0x0000u);
    }
    for (int i = 0; i < 10; ++i) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        REQUIRE(r.reason != GBB_STOP_INVALID_STATE);
    }
    memset(frame, 0xFF, sizeof(frame));
    REQUIRE(gbb_copy_frame_rgb555(m, frame, sizeof(frame), 320u, &info) == GBB_OK);
    for (size_t y = 0; y < FRAME_H; ++y) {
        if (!hblank_row_matches(frame, y)) {
            printf("not ok 1 - row %zu is not uniform %04X (first pixel %04X)\n", y,
                   (unsigned)hblank_value(y), (unsigned)frame[y * FRAME_W]);
            REQUIRE(hblank_row_matches(frame, y));
        }
    }
    REQUIRE(gbb_accept_rgb555_distinct(frame, 320u) == FRAME_H);
    char hex[65];
    REQUIRE(gbb_accept_rgb555_digest(frame, 320u, hex) == 0);
    if (strcmp(hex, HBLANK_FRAME_DIGEST) != 0) {
        printf("observed digest %s\n", hex);
        REQUIRE(strcmp(hex, HBLANK_FRAME_DIGEST) == 0);
    }
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
    {"palette_compat_api_default", palette_compat_api_default},
    {"palette_compat_api_roundtrip", palette_compat_api_roundtrip},
    {"palette_compat_api_reject", palette_compat_api_reject},
    {"palette_compat_api_get_reject", palette_compat_api_get_reject},
    {"palette_compat_api_larger", palette_compat_api_larger},
    {"palette_compat_api_survives", palette_compat_api_survives},
    {"palette_compat_effect_next_frame", palette_compat_effect_next_frame},
    {"cgb_colour_hblank_rows", cgb_colour_hblank_rows},
};

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2;
    fixture_dir = argc == 3 ? argv[2] : NULL;
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        int rc = cases[i].fn();
        if (rc == 0) printf("ok 1 - %s\n", cases[i].name);
        return rc;
    }
    return 2;
}
