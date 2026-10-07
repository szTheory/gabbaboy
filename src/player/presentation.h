#ifndef GABBABOY_PLAYER_PRESENTATION_H
#define GABBABOY_PLAYER_PRESENTATION_H

#include <stdbool.h>

typedef struct {
    int x;
    int y;
    int width;
    int height;
    int scale;
} player_presentation_rect;

/* Returns false without modifying out_rect when the drawable is below native size. */
bool player_presentation_layout(int drawable_width, int drawable_height,
                                player_presentation_rect *out_rect);

#endif
