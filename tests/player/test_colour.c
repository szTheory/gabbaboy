#include "colour.h"

#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define W 160u
#define H 144u

static unsigned expand_independent(unsigned c) {
    /* The documented expansion, written out here so the player's copy is not its own oracle. */
    return (c << 3) | (c >> 2);
}

/* Every one of the 32768 RGB555 values appears in two frames, once with a tight pitch and once
 * with a padded one, and each output channel must match the formula with alpha 255. */
static int expand_all_values(size_t pitch_pixels) {
    static uint16_t pixels[H * 400u];
    static uint8_t rgba[W * H * 4u];
    for (unsigned frame = 0u; frame < 2u; ++frame) {
        memset(pixels, 0xA5, sizeof(pixels));
        for (unsigned y = 0u; y < H; ++y)
            for (unsigned x = 0u; x < W; ++x)
                pixels[y * pitch_pixels + x] = (uint16_t)((frame * W * H + y * W + x) & 0x7FFFu);
        player_rgb555_frame_to_rgba(pixels, pitch_pixels * 2u, rgba);
        for (unsigned y = 0u; y < H; ++y) {
            for (unsigned x = 0u; x < W; ++x) {
                const unsigned v = pixels[y * pitch_pixels + x];
                const uint8_t *px = rgba + (y * W + x) * 4u;
                REQUIRE(px[0] == expand_independent(v & 31u));
                REQUIRE(px[1] == expand_independent((v >> 5) & 31u));
                REQUIRE(px[2] == expand_independent((v >> 10) & 31u));
                REQUIRE(px[3] == 255u);
                REQUIRE(px[0] == gbb_accept_expand5(v & 31u));
            }
        }
    }
    return 0;
}

static int expand(void) {
    /* Pure red, green and blue singletons catch a channel swap even if the table were symmetric. */
    static uint16_t pixels[W * H];
    static uint8_t rgba[W * H * 4u];
    pixels[0] = 0x001Fu;
    pixels[1] = 0x03E0u;
    pixels[2] = 0x7C00u;
    pixels[3] = 0x0000u;
    pixels[4] = 0x7FFFu;
    player_rgb555_frame_to_rgba(pixels, W * 2u, rgba);
    REQUIRE(rgba[0] == 255u && rgba[1] == 0u && rgba[2] == 0u && rgba[3] == 255u);
    REQUIRE(rgba[4] == 0u && rgba[5] == 255u && rgba[6] == 0u && rgba[7] == 255u);
    REQUIRE(rgba[8] == 0u && rgba[9] == 0u && rgba[10] == 255u && rgba[11] == 255u);
    REQUIRE(rgba[12] == 0u && rgba[13] == 0u && rgba[14] == 0u && rgba[15] == 255u);
    REQUIRE(rgba[16] == 255u && rgba[17] == 255u && rgba[18] == 255u && rgba[19] == 255u);
    REQUIRE(expand_all_values(W) == 0);
    REQUIRE(expand_all_values(W + 8u) == 0);
    return 0;
}

static int title_token(void) {
    REQUIRE(strcmp(player_model_token(GBB_MODE_DMG), "DMG") == 0);
    REQUIRE(strcmp(player_model_token(GBB_MODE_CGB), "CGB") == 0);
    REQUIRE(strcmp(player_model_token(GBB_MODE_CGB_DMG_COMPAT), "CGB (DMG-compat)") == 0);
    REQUIRE(strcmp(player_model_token(GBB_MODE_NONE), "-") == 0);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "player_cgb_expand") == 0 ||
        strcmp(argv[1], "player_cgb_expand_mutant_rb_swap") == 0)
        return expand();
    if (strcmp(argv[1], "player_cgb_title_token") == 0) return title_token();
    return 2;
}
