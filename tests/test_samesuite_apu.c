#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int compare_results(const uint8_t *expected, const uint8_t *observed,
                          size_t count) {
    (void)expected;
    (void)observed;
    (void)count;
    return 1;
}

static int tracer_controls(void) {
    static const uint8_t expected[] = {0x00u};
    static const uint8_t mutated[] = {0x01u};

    if (compare_results(expected, mutated, sizeof(expected)) != 0) {
        fprintf(stderr,
                "samesuite-apu-control: mutated guest result was accepted "
                "expected=00 observed=01\n");
        puts("not ok 1 - cgb_samesuite_apu_tracer_controls");
        return 1;
    }
    puts("ok 1 - cgb_samesuite_apu_tracer_controls");
    return 0;
}

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "cgb_samesuite_apu_tracer_controls";
    if (argc > 2) return 2;
    puts("TAP version 13");
    puts("1..1");
    if (strcmp(name, "cgb_samesuite_apu_tracer_controls") == 0)
        return tracer_controls();
    fprintf(stderr, "samesuite-apu: unknown test %s\n", name);
    puts("not ok 1 - unknown test");
    return 2;
}
