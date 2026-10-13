#include "colour.h"

#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"

#define COLOUR_WIDTH 160u
#define COLOUR_HEIGHT 144u

void player_rgb555_frame_to_rgba(const uint16_t *pixels, size_t pitch_bytes,
                                 uint8_t *rgba) {
    for (size_t y = 0u; y < COLOUR_HEIGHT; ++y) {
        const uint16_t *row = (const uint16_t *)((const uint8_t *)pixels + y * pitch_bytes);
        for (size_t x = 0u; x < COLOUR_WIDTH; ++x) {
            const unsigned value = row[x];
            uint8_t *out = rgba + (y * COLOUR_WIDTH + x) * 4u;
            out[0] = gbb_accept_expand5(value & 31u);
            out[1] = gbb_accept_expand5((value >> 5) & 31u);
            out[2] = gbb_accept_expand5((value >> 10) & 31u);
            out[3] = 255u;
        }
    }
}

const char *player_model_token(uint32_t mode) {
    switch (mode) {
    case GBB_MODE_DMG: return "DMG";
    case GBB_MODE_CGB: return "CGB";
    case GBB_MODE_CGB_DMG_COMPAT: return "CGB (DMG-compat)";
    default: return "-";
    }
}
