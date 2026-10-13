/* Public-API colour cases (Phase 11). Links GabbaBoy::core only; no core internals.
 *
 * Usage: test_cgb_colour <case> */
#include "gabbaboy/gabbaboy.h"

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

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "cgb_colour_copy_frame_unsupported") == 0) {
        int rc = cgb_colour_copy_frame_unsupported();
        if (rc == 0) puts("ok 1 - cgb_colour_copy_frame_unsupported");
        return rc;
    }
    return 2;
}
