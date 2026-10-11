#include "../src/core/gabbaboy.c"

#include <stdio.h>

/* Single-TU white-box test: it includes the core source to reach the static
 * write8 and the instance layout, so it must not link GabbaBoy::core. */

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static int check(gbb_instance *m, uint8_t expect_on) {
    uint8_t on = 0xEEu;
    uint64_t changes = 0u;
    REQUIRE(gbb_rumble_state(m, &on, &changes) == GBB_OK);
    REQUIRE(on == expect_on);
    REQUIRE(changes == UINT64_MAX);
    return 0;
}

/* The rumble change counter saturates instead of wrapping to zero. */
static int mbc5_rumble_saturation(void) {
    static uint8_t rom[0x8000];
    rom[0x147u] = 0x1Eu;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x04u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    m->cart.rumble_changes = UINT64_MAX - 1u;

    write8(m, 0x4000u, 0x08u); /* line on: MAX - 1 -> MAX */
    REQUIRE(check(m, 1u) == 0);
    write8(m, 0x4000u, 0x00u); /* line off: stays at MAX */
    REQUIRE(check(m, 0u) == 0);
    write8(m, 0x4000u, 0x08u); /* line on again */
    REQUIRE(check(m, 1u) == 0);
    REQUIRE(gbb_reset(m) == GBB_OK); /* reset from line-on counts one more */
    REQUIRE(check(m, 0u) == 0);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc5_rumble_saturation") == 0) return mbc5_rumble_saturation();
    return 2;
}
