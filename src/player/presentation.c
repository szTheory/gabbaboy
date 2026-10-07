#include "presentation.h"

#include <stddef.h>

bool player_presentation_layout(int drawable_width, int drawable_height,
                                player_presentation_rect *out_rect) {
    if (out_rect == NULL || drawable_width < 160 || drawable_height < 144)
        return false;

    int scale = drawable_width / 160;
    const int vertical_scale = drawable_height / 144;
    if (vertical_scale < scale) scale = vertical_scale;
    if (scale < 1) return false;

    const player_presentation_rect result = {
        (drawable_width - 160 * scale) / 2,
        (drawable_height - 144 * scale) / 2,
        160 * scale,
        144 * scale,
        scale
    };
    *out_rect = result;
    return true;
}
