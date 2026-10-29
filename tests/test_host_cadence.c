/* D-11: the pure flush cadence, proven by boundary tables instead of by waiting thousands of frames.
 *
 *   test_host_cadence quiet|age|rtc_compare|generation_compare|retry
 *
 * Every case prints `PASS <case>` or `FAIL <case>` (exit 1). Links gabbaboy_host only: the state machine
 * has no clock, no I/O and no core, so this test is portable. The two cadence mutants build this same
 * source against an edited host_cadence.c and must fail their own case. */
#include "gbb_host.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Quiet period: one change at frame 100 flushes exactly 16 frames later, not 15 and not 17. */
static int quiet(void) {
    host_cadence cadence;
    host_cadence_reset(&cadence, 0u, 0u);
    for (uint64_t frame = 0u; frame < 100u; ++frame)
        REQUIRE(host_cadence_step(&cadence, frame, 0u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 100u, 1u) == HOST_CADENCE_NONE); /* the change itself */
    REQUIRE(cadence.dirty);
    for (uint64_t frame = 101u; frame <= 115u; ++frame)
        REQUIRE(host_cadence_step(&cadence, frame, 1u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 116u, 1u) == HOST_CADENCE_FLUSH);
    return 0;
}

/* Age cap: a guest that writes every frame never goes quiet, so the first unflushed change forces a
 * flush at 300 frames: 299 frames old is not due, 300 is. */
static int age(void) {
    host_cadence cadence;
    host_cadence_reset(&cadence, 0u, 0u);
    for (uint64_t frame = 100u; frame <= 399u; ++frame)
        REQUIRE(host_cadence_step(&cadence, frame, frame - 99u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 400u, 301u) == HOST_CADENCE_FLUSH);
    return 0;
}

/* RTC-only drift does not bump the generation, so a clean image is exported and compared every
 * 3,600 frames, counted from the last flush or compare. */
static int rtc_compare(void) {
    host_cadence cadence;
    host_cadence_reset(&cadence, 0u, 0u);
    REQUIRE(host_cadence_step(&cadence, 3599u, 0u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 3600u, 0u) == HOST_CADENCE_EXPORT_COMPARE);
    host_cadence_flushed(&cadence, 0u, 3600u);
    REQUIRE(host_cadence_step(&cadence, 7199u, 0u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 7200u, 0u) == HOST_CADENCE_EXPORT_COMPARE);
    /* A frame below a stored mark reads as age zero; unsigned subtraction must not wrap. */
    host_cadence_reset(&cadence, 0u, 1000u);
    REQUIRE(host_cadence_step(&cadence, 10u, 0u) == HOST_CADENCE_NONE);
    return 0;
}

/* The generation is compared with !=: a decrease (a state load or an import moves the counter
 * backwards) is a change too, and an unchanged value is not. */
static int generation_compare(void) {
    host_cadence cadence;
    host_cadence_reset(&cadence, 7u, 0u);
    REQUIRE(host_cadence_step(&cadence, 5u, 7u) == HOST_CADENCE_NONE);
    REQUIRE(!cadence.dirty); /* equal generation: nothing to flush */
    REQUIRE(host_cadence_step(&cadence, 10u, 5u) == HOST_CADENCE_NONE);
    REQUIRE(cadence.dirty);  /* 7 -> 5 is a change */
    REQUIRE(host_cadence_step(&cadence, 25u, 5u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 26u, 5u) == HOST_CADENCE_FLUSH);
    host_cadence_flushed(&cadence, 5u, 26u);
    REQUIRE(!cadence.dirty);
    REQUIRE(host_cadence_step(&cadence, 30u, 9u) == HOST_CADENCE_NONE); /* an increase also counts */
    REQUIRE(cadence.dirty);
    return 0;
}

/* A failed flush keeps the image dirty and retries 16 frames later; `flushed` advances only after the
 * writer succeeds. */
static int retry(void) {
    host_cadence cadence;
    host_cadence_reset(&cadence, 0u, 0u);
    REQUIRE(host_cadence_step(&cadence, 10u, 1u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 26u, 1u) == HOST_CADENCE_FLUSH);
    host_cadence_flush_failed(&cadence, 26u);
    REQUIRE(cadence.dirty);
    REQUIRE(cadence.flushed_generation == 0u); /* not advanced by a failure */
    REQUIRE(host_cadence_step(&cadence, 41u, 1u) == HOST_CADENCE_NONE);
    REQUIRE(host_cadence_step(&cadence, 42u, 1u) == HOST_CADENCE_FLUSH);
    host_cadence_flushed(&cadence, 1u, 42u);
    REQUIRE(!cadence.dirty);
    REQUIRE(cadence.flushed_generation == 1u);
    REQUIRE(host_cadence_step(&cadence, 43u, 1u) == HOST_CADENCE_NONE);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_host_cadence <case>\n");
        return 2;
    }
    static const struct { const char *name; int (*run)(void); } cases[] = {
        {"quiet", quiet}, {"age", age}, {"rtc_compare", rtc_compare},
        {"generation_compare", generation_compare}, {"retry", retry}
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        if (cases[i].run() != 0) {
            printf("FAIL %s\n", cases[i].name);
            return 1;
        }
        printf("PASS %s\n", cases[i].name);
        return 0;
    }
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
