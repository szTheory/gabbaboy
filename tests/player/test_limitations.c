#include "limitations.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    static const char expected[] =
        "Audio is not implemented. Battery saves support standard MBC1 type $03 with 8 or 32 KiB RAM.";

    if (strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected) != 0) {
        fprintf(stderr, "player limitation text differs from the supported preview claim\n");
        return 1;
    }
    return 0;
}
