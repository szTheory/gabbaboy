#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size);

int main(void) {
    static const uint8_t minimized_decoder_crash[] = {
        0xFFu, 0x00u, 0x00u, 0x08u, 0x00u,
        0x00u, 0x1Cu, 0x00u, 0x08u, 0x00u
    };
    static const uint8_t over_limit = 0xFFu;
    if (gbb_fuzz_core_one_input(minimized_decoder_crash,
                                sizeof(minimized_decoder_crash)) != 0) {
        fprintf(stderr, "minimized fuzz decoder reproducer failed\n");
        return 1;
    }
    if (gbb_fuzz_core_one_input(NULL, 0u) != 0 ||
        gbb_fuzz_core_one_input(&over_limit, 65537u) != 0) {
        fprintf(stderr, "fuzz input size bounds failed\n");
        return 1;
    }
    return 0;
}
