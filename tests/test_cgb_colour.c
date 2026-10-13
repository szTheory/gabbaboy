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

/* ---- Original fixtures: colour-attr.gb and colour-lcdc0.gb (D-23 items 1, 2 and 6) ---- */
/* Ten 16x16 cells in one row. Each cell is 2x2 copies of one 8x8 tile of four 4x4 quadrants, so a
 * cell's expected colours are four literals typed here from the fixture design in the manifest
 * protocol (never read back from the core). Quadrant order: TL, TR, BL, BR. */
#define ATTR_CELLS 10u
#define ATTR_BLANK 0x1111u   /* BG palette 0 colour 0 */
static const uint16_t attr_expected[ATTR_CELLS][4] = {
    {0x6666u, 0x7777u, 0x4321u, 0x5555u},   /* 0 BG palette 3 */
    {0x0444u, 0x1111u, 0x2222u, 0x3333u},   /* 1 tile bank 1 */
    {0x3333u, 0x2222u, 0x1111u, 0x0444u},   /* 2 X flip */
    {0x0444u, 0x1111u, 0x2222u, 0x3333u},   /* 3 Y flip */
    {0x2222u, 0x3333u, 0x0444u, 0x1111u},   /* 4 attr bit 4 set: equals cell 8 */
    {0x2222u, 0x2222u, 0x2222u, 0x2222u},   /* 5 BG priority bit: the BG wins over the object */
    {0x1BCDu, 0x1111u, 0x789Au, 0x0ABCu},   /* 6 OBJ bank 1, palette 5 (index 0 shows the BG) */
    {0x4567u, 0x5678u, 0x6789u, 0x1111u},   /* 7 OBJ bank 0, palette 2 */
    {0x2222u, 0x3333u, 0x0444u, 0x1111u},   /* 8 reference: attr 0 */
    {0x1111u, 0x1111u, 0x1111u, 0x1111u},   /* 9 blank */
};
#define ATTR_OBJ_OVER_BG 0x1234u   /* OBJ palette 0 colour 1: cell 5 when LCDC bit 0 is clear */

static unsigned attr_quadrant(size_t x, size_t y) { return (unsigned)((y % 8u) / 4u * 2u + (x % 8u) / 4u); }

/* Returns 0 when every pixel matches; prints the first mismatch. `cell5` replaces cell 5's colour. */
static int attr_frame_matches(const uint16_t *frame, uint16_t cell5) {
    for (size_t y = 0; y < FRAME_H; ++y) {
        for (size_t x = 0; x < FRAME_W; ++x) {
            const size_t cell = x / 16u;
            uint16_t want = ATTR_BLANK;
            if (y < 16u) want = cell == 5u ? cell5 : attr_expected[cell][attr_quadrant(x, y)];
            if (frame[y * FRAME_W + x] != want) {
                printf("not ok 1 - cell %zu pixel (%zu,%zu) is %04X, expected %04X\n", cell, x, y,
                       (unsigned)frame[y * FRAME_W + x], (unsigned)want);
                return 1;
            }
        }
    }
    return 0;
}

/* Cell 4 must equal the attr-0 reference cell 8, pixel for pixel (bit 4 is an unused attribute bit). */
static int attr_bit4_equals_reference(const uint16_t *frame) {
    for (size_t y = 0; y < 16u; ++y)
        for (size_t x = 0; x < 16u; ++x)
            if (frame[y * FRAME_W + 4u * 16u + x] != frame[y * FRAME_W + 8u * 16u + x]) return 1;
    return 0;
}

static int run_fixture_frame(const char *name, gbb_profile profile, uint16_t *frame, gbb_instance **out) {
    static uint8_t rom[ROM_SIZE];
    gbb_frame_info info;
    gbb_instance *m = NULL;
    REQUIRE(read_fixture(name, rom, sizeof(rom)) == ROM_SIZE);
    REQUIRE(gbb_create(profile, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    for (int i = 0; i < 10; ++i) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        REQUIRE(r.reason != GBB_STOP_INVALID_STATE);
    }
    memset(frame, 0xFF, sizeof(uint16_t) * FRAME_W * FRAME_H);
    REQUIRE(gbb_copy_frame_rgb555(m, frame, sizeof(uint16_t) * FRAME_W * FRAME_H, 320u, &info) == GBB_OK);
    *out = m;
    return 0;
}

static int check_digest(const uint16_t *frame, const char *want) {
    char hex[65];
    REQUIRE(gbb_accept_rgb555_digest(frame, 320u, hex) == 0);
    if (strcmp(hex, want) != 0) {
        printf("observed digest %s\n", hex);
        REQUIRE(strcmp(hex, want) == 0);
    }
    return 0;
}

#define ATTR_FRAME_DIGEST "38f5419acf11682ef8054b7d568b136b236ff807985d26f9ca1485a6ce9f3c52"
#define LCDC0_FRAME_DIGEST "e3c3f19f2c201c9f092e006b5c9dfee718af3cf571a5b73f78df44a5e15da1b8"

static int cgb_colour_attr(void) {
    static uint16_t frame[FRAME_W * FRAME_H];
    gbb_instance *m = NULL;
    if (run_fixture_frame("colour-attr.gb", GBB_PROFILE_CGB_CPU_E, frame, &m) != 0) return 1;
    REQUIRE(attr_frame_matches(frame, 0x2222u) == 0);
    REQUIRE(attr_bit4_equals_reference(frame) == 0);
    REQUIRE(check_digest(frame, ATTR_FRAME_DIGEST) == 0);
    gbb_destroy(m);
    return 0;
}

/* D-06: with LCDC bit 0 clear the BG is still drawn with its colours; only the priority bit's
 * force-the-BG-on-top effect goes away, so cell 5 shows the object. */
static int cgb_colour_lcdc0(void) {
    static uint16_t frame[FRAME_W * FRAME_H];
    gbb_instance *m = NULL;
    if (run_fixture_frame("colour-lcdc0.gb", GBB_PROFILE_CGB_CPU_E, frame, &m) != 0) return 1;
    REQUIRE(attr_frame_matches(frame, ATTR_OBJ_OVER_BG) == 0);
    REQUIRE(attr_bit4_equals_reference(frame) == 0);
    REQUIRE(frame[0] == 0x6666u);   /* a BG cell is drawn although LCDC bit 0 is clear */
    REQUIRE(check_digest(frame, LCDC0_FRAME_DIGEST) == 0);
    gbb_destroy(m);
    return 0;
}

/* ---- Original fixture: colour-cram.gb (D-23 item 3, D-11) ---- */
/* The guest reports through WRAM, never through a register predicate: $C000 is the verdict
 * ($A5 pass / $EE fail) and $C001..$C007 are one byte per cell ($01 pass). */
static int cgb_colour_guest_cram(void) {
    static uint8_t rom[ROM_SIZE];
    gbb_instance *m = NULL;
    REQUIRE(read_fixture("colour-cram.gb", rom, sizeof(rom)) == ROM_SIZE);
    REQUIRE(rom[0x143u] == 0x80u);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    for (int i = 0; i < 10; ++i) {
        gbb_run_result r = gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        REQUIRE(r.reason != GBB_STOP_INVALID_STATE);
    }
    for (uint16_t cell = 1u; cell <= 7u; ++cell) {
        const uint8_t got = gbb_peek_ram(m, (uint16_t)(0xC000u + cell));
        if (got != 0x01u) printf("not ok 1 - cell %u byte C%03X is %02X, expected 01\n", (unsigned)cell,
                                 (unsigned)cell, (unsigned)got);
        REQUIRE(got == 0x01u);
    }
    const uint8_t verdict = gbb_peek_ram(m, 0xC000u);
    if (verdict != 0xA5u) printf("not ok 1 - verdict C000=%02X, expected A5\n", (unsigned)verdict);
    REQUIRE(verdict == 0xA5u);
    gbb_destroy(m);
    return 0;
}

/* ---- Original fixture: colour-compat.gb (D-23 item 5, D-17, D-39) ---- */
/* BGP = $E4, OBP0 = $E4, OBP1 = $1B. Bars x 0..63 show BG indices 0-3; objects at y 0..7: OBJ0
 * indices 1-3 at x 80..103 (identity) and OBJ1 indices 1-3 at x 112..135 (reversed, so index n is
 * shade 3 - n); every other pixel is BG index 0. */
static uint16_t compat_expected(const gbb_compat_palette *p, size_t x, size_t y) {
    if (x < 64u) return p->bg[x / 16u];
    if (y < 8u && x >= 80u && x < 104u) return p->obj0[1u + (x - 80u) / 8u];
    if (y < 8u && x >= 112u && x < 136u) return p->obj1[2u - (x - 112u) / 8u];
    return p->bg[0];
}

static int compat_frame_matches(const uint16_t *frame, const gbb_compat_palette *p) {
    for (size_t y = 0; y < FRAME_H; ++y) {
        for (size_t x = 0; x < FRAME_W; ++x) {
            const uint16_t want = compat_expected(p, x, y);
            if (frame[y * FRAME_W + x] != want) {
                printf("not ok 1 - pixel (%zu,%zu) is %04X, expected %04X\n", x, y,
                       (unsigned)frame[y * FRAME_W + x], (unsigned)want);
                return 1;
            }
        }
    }
    return 0;
}

#define COMPAT_DEFAULT_DIGEST "f08a99fe95516a498ec8028fe3a95b9afc916bab808fd13b9aae1b0b96aae7a5"
#define COMPAT_OVERRIDE_DIGEST "ed14c6c4166cfc0475116d5bed7582745acea6d16512d727d6806ec467d3aa01"

static int palette_compat_mapping(void) {
    static uint16_t before[FRAME_W * FRAME_H], after[FRAME_W * FRAME_H];
    gbb_compat_palette deflt, override = distinct_palette();
    gbb_frame_info info;
    gbb_instance *m = NULL;
    for (int i = 0; i < 4; ++i) deflt.bg[i] = deflt.obj0[i] = deflt.obj1[i] = default_ramp[i];
    deflt.struct_size = GBB_COMPAT_PALETTE_SIZE_V1;
    if (run_fixture_frame("colour-compat.gb", GBB_PROFILE_CGB_CPU_E, before, &m) != 0) return 1;
    /* D-17: the default palette, each region through its own BGP/OBP0/OBP1 mapping. */
    REQUIRE(compat_frame_matches(before, &deflt) == 0);
    REQUIRE(check_digest(before, COMPAT_DEFAULT_DIGEST) == 0);
    /* D-39: the override applies to the next completed frame, per palette set. */
    REQUIRE(gbb_set_compat_palette(m, &override) == GBB_OK);
    for (int i = 0; i < 2; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    memset(after, 0xFF, sizeof(after));
    REQUIRE(gbb_copy_frame_rgb555(m, after, sizeof(after), 320u, &info) == GBB_OK);
    REQUIRE(compat_frame_matches(after, &override) == 0);
    for (size_t y = 0; y < FRAME_H; ++y)         /* every region changed */
        for (size_t x = 0; x < FRAME_W; ++x)
            REQUIRE(after[y * FRAME_W + x] != before[y * FRAME_W + x]);
    REQUIRE(check_digest(after, COMPAT_OVERRIDE_DIGEST) == 0);
    gbb_destroy(m);
    return 0;
}

/* ---- Original fixture: colour-lcdoff.gb (D-23 item 7, D-02) ---- */
#define LCDOFF_COLOUR 0x2A55u
#define LCDOFF_DIGEST "ad26a2e9df3b30fe1e6117cd6d920547ebe8d4ebb40f376562f55488d70b3e81"

static int cgb_colour_lcd_off(void) {
    static uint8_t rom[ROM_SIZE];
    static uint16_t first[FRAME_W * FRAME_H], later[FRAME_W * FRAME_H];
    gbb_frame_info a, b;
    gbb_instance *m = NULL;
    int marker = 0;
    REQUIRE(read_fixture("colour-lcdoff.gb", rom, sizeof(rom)) == ROM_SIZE);
    REQUIRE(gbb_create(GBB_PROFILE_CGB_CPU_E, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    for (int i = 0; i < 30 && !marker; ++i) {
        gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
        marker = gbb_peek_ram(m, 0xC000u) == 0xA5u;
    }
    REQUIRE(marker);
    gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, first, sizeof(first), 320u, &a) == GBB_OK);
    for (size_t i = 0; i < (size_t)FRAME_W * FRAME_H; ++i) REQUIRE(first[i] == LCDOFF_COLOUR);
    for (int i = 0; i < 5; ++i) gbb_run(m, FRAME_HALF_DOTS, NULL, 0);
    REQUIRE(gbb_copy_frame_rgb555(m, later, sizeof(later), 320u, &b) == GBB_OK);
    REQUIRE(a.generation >= 1u && b.generation == a.generation);
    REQUIRE(memcmp(first, later, sizeof(first)) == 0);
    REQUIRE(check_digest(later, LCDOFF_DIGEST) == 0);
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
    {"cgb_colour_attr", cgb_colour_attr},
    {"cgb_colour_lcdc0", cgb_colour_lcdc0},
    {"cgb_colour_guest_cram", cgb_colour_guest_cram},
    {"palette_compat_mapping", palette_compat_mapping},
    {"cgb_colour_lcd_off", cgb_colour_lcd_off},
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
