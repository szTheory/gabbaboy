/* Emit the original, non-artwork replacement for Mooneye's bundled font.
 * The 2032-byte all-zero image preserves the include's exact size and ROM
 * layout while carrying no third-party font glyphs. */
#include <stdio.h>

int main(int argc, char **argv)
{
    FILE *output;
    unsigned char blank[2032] = {0};

    if (argc != 2) {
        (void)fprintf(stderr, "usage: %s OUTPUT\n", argv[0]);
        return 2;
    }
    output = fopen(argv[1], "wb");
    if (output == NULL) {
        perror(argv[1]);
        return 1;
    }
    if (fwrite(blank, 1, sizeof blank, output) != sizeof blank) {
        (void)fclose(output);
        (void)fprintf(stderr, "could not write replacement font asset\n");
        return 1;
    }
    if (fclose(output) != 0) {
        (void)fprintf(stderr, "could not close replacement font asset\n");
        return 1;
    }
    return 0;
}
