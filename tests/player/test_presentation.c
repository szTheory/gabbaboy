#include "presentation.h"

#include <limits.h>
#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static int expect_layout(const char *name, int drawable_width, int drawable_height,
                         int scale, int x, int y) {
    player_presentation_rect rect;
    REQUIRE(player_presentation_layout(drawable_width, drawable_height, &rect));
    REQUIRE(rect.scale == scale && rect.x == x && rect.y == y);
    REQUIRE(rect.width == 160 * scale && rect.height == 144 * scale);
    (void)name;
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const char *name = argv[1];
    if (strcmp(name, "player_presentation_native") == 0)
        return expect_layout(name, 160, 144, 1, 0, 0);
    if (strcmp(name, "player_presentation_integer") == 0)
        return expect_layout(name, 320, 288, 2, 0, 0);
    if (strcmp(name, "player_presentation_odd") == 0)
        return expect_layout(name, 327, 299, 2, 3, 5);
    if (strcmp(name, "player_presentation_letterbox") == 0)
        return expect_layout(name, 400, 300, 2, 40, 6);
    if (strcmp(name, "player_presentation_hidpi") == 0)
        return expect_layout(name, 640, 576, 4, 0, 0);
    if (strcmp(name, "player_presentation_resize") == 0) {
        REQUIRE(expect_layout(name, 320, 288, 2, 0, 0) == 0);
        return expect_layout(name, 640, 576, 4, 0, 0);
    }
    if (strcmp(name, "player_presentation_undersized") == 0) {
        player_presentation_rect rect = {7, 11, 13, 17, 19};
        const player_presentation_rect before = rect;
        REQUIRE(!player_presentation_layout(159, 144, &rect));
        REQUIRE(memcmp(&rect, &before, sizeof(rect)) == 0);
        REQUIRE(!player_presentation_layout(160, 143, &rect));
        REQUIRE(!player_presentation_layout(0, 0, &rect));
        REQUIRE(!player_presentation_layout(-1, 144, &rect));
        return 0;
    }
    if (strcmp(name, "player_presentation_large") == 0) {
        player_presentation_rect rect;
        REQUIRE(player_presentation_layout(INT_MAX, INT_MAX, &rect));
        REQUIRE(rect.scale == INT_MAX / 160);
        REQUIRE(rect.width <= INT_MAX && rect.height <= INT_MAX);
        REQUIRE(rect.x >= 0 && rect.y >= 0);
        REQUIRE(rect.x + rect.width <= INT_MAX);
        REQUIRE(rect.y + rect.height <= INT_MAX);
        return 0;
    }
    return 2;
}
