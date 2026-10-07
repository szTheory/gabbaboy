#include "limitations.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    static const char expected[] =
        "Audio and battery-save persistence are not implemented.";

    if (strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected) != 0) {
        fprintf(stderr, "player limitation text differs from the supported preview claim\n");
        return 1;
    }
    return 0;
}
