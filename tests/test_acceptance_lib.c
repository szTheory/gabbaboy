#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("PASS %s\n", name); return 0; } while (0)

/* Bounded whole-file read; the caller frees the buffer. */
static uint8_t *read_file(const char *path, size_t capacity, size_t *length) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    uint8_t *buffer = malloc(capacity + 1u);
    if (buffer == NULL) { fclose(f); return NULL; }
    size_t n = fread(buffer, 1, capacity + 1u, f);
    int failed = ferror(f);
    fclose(f);
    if (failed || n > capacity) { free(buffer); return NULL; }
    *length = n;
    return buffer;
}

static int case_libbet_replay(const char *rom_path, const char *script_path) {
    size_t rom_length = 0, script_length = 0;
    uint8_t *rom = read_file(rom_path, 32768u, &rom_length);
    uint8_t *script_bytes = read_file(script_path, GBB_ACCEPT_SCRIPT_MAX_BYTES, &script_length);
    gbb_instance *instance = NULL;
    gbb_accept_script script;
    memset(&script, 0, sizeof(script));
    int rc = 1;
    char digest[65], err[160];
    const gbb_accept_predicate *predicate = NULL;
    gbb_accept_stepper *stepper = NULL;

    if (rom == NULL || script_bytes == NULL) { fprintf(stderr, "cannot read inputs\n"); goto done; }
    gbb_accept_sha256_hex(rom, rom_length, digest);
    predicate = gbb_accept_predicate_find("libbet-tutorial-cleared", digest);
    if (predicate == NULL) { fprintf(stderr, "predicate not bound to ROM %s\n", digest); goto done; }
    if (gbb_accept_script_parse(script_bytes, script_length, &script, err, sizeof(err)) != 0) {
        fprintf(stderr, "%s\n", err);
        goto done;
    }
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) != GBB_OK) goto done;
    if (gbb_load_rom(instance, rom, rom_length) != GBB_OK) goto done;
    stepper = malloc(sizeof(*stepper));
    if (stepper == NULL) goto done;
    gbb_accept_stepper_init(stepper, instance, NULL, NULL);

    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = stepper;
    config.script = &script;
    config.predicate = predicate;
    config.expect_hw = 0;
    config.budget_half_dots = 3600u * GBB_ACCEPT_HALF_DOTS_PER_FRAME; /* D-13: 3600f */
    config.tail_half_dots = GBB_ACCEPT_TAIL_HALF_DOTS;
    config.max_batch = 32;
    gbb_accept_drive_result result;
    gbb_accept_drive(&config, &result);
    if (result.status != GBB_ACCEPT_DRIVE_HIT) {
        fprintf(stderr, "drive status=%d stop=%d end=%llu\n", (int)result.status,
                (int)result.stop_reason, (unsigned long long)result.end_half_dots);
        goto done;
    }
    printf("lib_replay status=hit t_hit_half_dots=%llu\n", (unsigned long long)result.t_hit_half_dots);
    rc = 0;
done:
    free(stepper);
    gbb_accept_script_free(&script);
    gbb_destroy(instance);
    free(script_bytes);
    free(rom);
    if (rc == 0) printf("PASS acceptance_lib_libbet_replay\n");
    return rc;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: test_acceptance_lib <case> [args]\n"); return 2; }
    if (strcmp(argv[1], "acceptance_lib_libbet_replay") == 0) {
        REQUIRE(argc == 4);
        return case_libbet_replay(argv[2], argv[3]);
    }
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
