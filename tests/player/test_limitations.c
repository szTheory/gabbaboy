#include "limitations.h"

#include <stdio.h>
#include <string.h>

int main(void) {
    static const char expected[] =
        "Audio is not implemented. Battery saves support only the current MBC1 type $03 8 KiB RAM profile.";

    if (strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected) != 0) {
        fprintf(stderr, "player limitation text differs from the supported preview claim\n");
        return 1;
    }
    return 0;
}
