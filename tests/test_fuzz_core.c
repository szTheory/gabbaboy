#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

int gbb_fuzz_core_one_input(const uint8_t *data, size_t size);

int main(void) {
    static const uint8_t minimized_decoder_crash[] = {
        0xFFu, 0x00u, 0x00u, 0x08u, 0x00u,
        0x00u, 0x1Cu, 0x00u, 0x08u, 0x00u
    };
    static const uint8_t seed_declared[] = {0x02u, 0x13u, 0x00u, 0x02u, 0x00u};
    static const uint8_t seed_declared_minus_1[] = {0x02u, 0x10u, 0x01u, 0x03u, 0x01u};
    static const uint8_t seed_declared_plus_1[] = {0x02u, 0x10u, 0x02u, 0x00u, 0x02u};
    static const uint8_t seed_mib2[] = {0x02u, 0x0Fu, 0x06u, 0x00u, 0x03u};
    static const uint8_t seed_mib2_plus_1[] = {0x02u, 0x01u, 0x06u, 0x00u, 0x04u};
    static const uint8_t seed_mib4[] = {0x02u, 0x0Fu, 0x07u, 0x00u, 0x05u};
    static const uint8_t seed_mib4_plus_1[] = {0x02u, 0x10u, 0x07u, 0x02u, 0x06u};
    static const uint8_t seed_mib8[] = {0x02u, 0x19u, 0x08u, 0x00u, 0x07u};
    static const uint8_t seed_mib8_plus_1[] = {0x02u, 0x19u, 0x08u, 0x00u, 0x08u};
    static const uint8_t seed_size_max[] = {0x02u, 0xFFu, 0xFFu, 0xFFu, 0x09u};
    static const uint8_t seed_short[] = {0x02u, 0x10u};
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
    if (
        gbb_fuzz_core_one_input(seed_declared, sizeof(seed_declared)) != 0 ||
        gbb_fuzz_core_one_input(seed_declared_minus_1, sizeof(seed_declared_minus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_declared_plus_1, sizeof(seed_declared_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib2, sizeof(seed_mib2)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib2_plus_1, sizeof(seed_mib2_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib4, sizeof(seed_mib4)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib4_plus_1, sizeof(seed_mib4_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib8, sizeof(seed_mib8)) != 0 ||
        gbb_fuzz_core_one_input(seed_mib8_plus_1, sizeof(seed_mib8_plus_1)) != 0 ||
        gbb_fuzz_core_one_input(seed_size_max, sizeof(seed_size_max)) != 0 ||
        gbb_fuzz_core_one_input(seed_short, sizeof(seed_short)) != 0) {
        fprintf(stderr, "synthesised-length fuzz seed failed\n");
        return 1;
    }
    return 0;
}
