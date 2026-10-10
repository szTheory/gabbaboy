#include "acceptance.h"
#include "gbb_accept.h"

#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Acceptance orchestration. Every input (script digest and syntax, ROM size
 * and digest, predicate binding) is validated before any instance exists, so
 * a bad case never partially executes (T-07-08). The stepping loop is the
 * shared gbb_accept_drive with the default gbb_queue_events delivery. */

#define EXIT_PASS 0
#define EXIT_FAIL 1
#define EXIT_INVALID 2
#define EXIT_UNSUPPORTED 3
#define DRIVE_MAX_BATCH 64u

int gbb_runner_read_file(const char *path, size_t capacity, uint8_t **out, size_t *length) {
    *out = NULL;
    *length = 0;
    FILE *file = fopen(path, "rb");
    if (file == NULL) return 1;
    uint8_t *buffer = malloc(capacity + 1u);
    if (buffer == NULL) {
        fclose(file);
        return 3;
    }
    size_t n = fread(buffer, 1, capacity + 1u, file);
    int failed = ferror(file);
    if (fclose(file) != 0) failed = 1;
    if (failed || n > capacity) {
        free(buffer);
        return 2;
    }
    *out = buffer;
    *length = n;
    return 0;
}

static int input_error(const gbb_case *c, const char *reason) {
    fprintf(stderr, "acceptance id=%s status=invalid reason=%s\n", c->id, reason);
    return EXIT_INVALID;
}

int gbb_acceptance_run_case(const gbb_case *c, const gbb_acceptance_options *options) {
    uint8_t *script_bytes = NULL, *rom = NULL;
    size_t script_length = 0, rom_length = 0;
    gbb_accept_script script;
    gbb_accept_stepper *stepper = NULL;
    gbb_instance *instance = NULL;
    char digest[65], err[160];
    int code = EXIT_INVALID;
    memset(&script, 0, sizeof(script));

    if (c->oracle != GBB_ORACLE_PROGRESS_PREDICATE) {
        /* Frame-digest oracles are wired by a later plan; refuse rather than guess. */
        fprintf(stderr, "acceptance id=%s status=unsupported reason=unsupported-oracle\n", c->id);
        return EXIT_UNSUPPORTED;
    }

    /* Input script: digest over the raw bytes first, then syntax. */
    int rc = gbb_runner_read_file(c->input_script, GBB_ACCEPT_SCRIPT_MAX_BYTES, &script_bytes, &script_length);
    if (rc != 0) { code = input_error(c, rc == 1 ? "input-missing" : "input-unreadable"); goto done; }
    gbb_accept_sha256_hex(script_bytes, script_length, digest);
    if (strcmp(digest, c->input_sha256) != 0) { code = input_error(c, "input-digest-mismatch"); goto done; }
    rc = gbb_accept_script_parse(script_bytes, script_length, &script, err, sizeof(err));
    if (rc != 0) {
        fprintf(stderr, "acceptance id=%s status=invalid reason=invalid-script detail=\"%s\"\n", c->id, rc == 1 ? err : "allocation");
        goto done;
    }

    /* ROM: bounded heap load, exact size and digest before gbb_load_rom (D-27). */
    rc = gbb_runner_read_file(c->rom, GBB_CASES_MAX_ROM_BYTES, &rom, &rom_length);
    if (rc != 0) { code = input_error(c, rc == 1 ? "rom-missing" : "rom-unreadable"); goto done; }
    if (rom_length != c->rom_size) { code = input_error(c, "rom-size-mismatch"); goto done; }
    gbb_accept_sha256_hex(rom, rom_length, digest);
    if (strcmp(digest, c->rom_sha256) != 0) { code = input_error(c, "rom-digest-mismatch"); goto done; }

    /* The predicate is bound to a ROM digest and its anchors must still match. */
    const gbb_accept_predicate *predicate = gbb_accept_predicate_find(c->predicate, digest);
    if (predicate == NULL) { code = input_error(c, "predicate-not-bound"); goto done; }
    if (!gbb_accept_predicate_anchors_match(predicate, rom, rom_length)) {
        code = input_error(c, "predicate-anchor-mismatch");
        goto done;
    }

    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) != GBB_OK) {
        fprintf(stderr, "runner-error: instance allocation failed\n");
        goto done;
    }
    if (gbb_load_rom(instance, rom, rom_length) != GBB_OK) { code = input_error(c, "rom-rejected"); goto done; }
    stepper = malloc(sizeof(*stepper)); /* carries a PCM buffer: keep it off the stack */
    if (stepper == NULL) {
        fprintf(stderr, "runner-error: stepper allocation failed\n");
        goto done;
    }
    gbb_accept_stepper_init(stepper, instance, NULL, NULL);

    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = stepper;
    config.script = &script;
    config.predicate = predicate;
    config.expect_hw = c->expect_hw_capability;
    config.budget_half_dots = c->budget_half_dots;
    config.tail_half_dots = 0; /* the verdict is T_hit; no post-hit run is needed here */
    config.max_batch = DRIVE_MAX_BATCH;
    gbb_accept_drive_result result;
    gbb_accept_drive(&config, &result);

    switch (result.status) {
    case GBB_ACCEPT_DRIVE_HIT:
        printf("acceptance id=%s status=pass model=dmg-cpu-b t_hit_half_dots=%llu\n", c->id,
               (unsigned long long)result.t_hit_half_dots);
        if (options != NULL && options->receipt) {
            printf("receipt id=%s rom_sha256=%s rom_size=%u input_sha256=%s predicate=%s "
                   "budget_half_dots=%llu end_half_dots=%llu core_revision=%s build_qualified=%s\n",
                   c->id, c->rom_sha256, (unsigned)c->rom_size, c->input_sha256, c->predicate,
                   (unsigned long long)c->budget_half_dots,
                   (unsigned long long)result.end_half_dots,
                   options->core_revision != NULL ? options->core_revision : "unknown",
                   options->build_qualified ? "true" : "false");
        }
        code = EXIT_PASS;
        break;
    case GBB_ACCEPT_DRIVE_NOT_REACHED:
        printf("acceptance id=%s status=fail model=dmg-cpu-b reason=predicate-not-reached end_half_dots=%llu\n",
               c->id, (unsigned long long)result.end_half_dots);
        code = EXIT_FAIL;
        break;
    case GBB_ACCEPT_DRIVE_STOPPED:
        printf("acceptance id=%s status=unsupported model=dmg-cpu-b reason=guest-stopped stop=%d end_half_dots=%llu\n",
               c->id, (int)result.stop_reason, (unsigned long long)result.end_half_dots);
        code = EXIT_UNSUPPORTED;
        break;
    case GBB_ACCEPT_DRIVE_GUARD:
        printf("acceptance id=%s status=unsupported model=dmg-cpu-b reason=step-guard end_half_dots=%llu\n",
               c->id, (unsigned long long)result.end_half_dots);
        code = EXIT_UNSUPPORTED;
        break;
    default:
        printf("acceptance id=%s status=unsupported model=dmg-cpu-b reason=drive-error status_code=%d\n",
               c->id, (int)result.status);
        code = EXIT_UNSUPPORTED;
        break;
    }

done:
    free(stepper);
    gbb_destroy(instance);
    gbb_accept_script_free(&script);
    free(rom);
    free(script_bytes);
    return code;
}

int gbb_acceptance_run_file(const char *cases_path, const char *case_id,
                            const gbb_acceptance_options *options) {
    uint8_t *bytes = NULL;
    size_t length = 0;
    int rc = gbb_runner_read_file(cases_path, GBB_CASES_MAX_BYTES, &bytes, &length);
    if (rc == 2) {
        fprintf(stderr, "invalid-cases: file-too-large line=0\n");
        return EXIT_INVALID;
    }
    if (rc != 0) {
        fprintf(stderr, "invalid-cases: %s line=0\n", rc == 1 ? "file-missing" : "allocation-failed");
        return EXIT_INVALID;
    }
    gbb_case_list list;
    char err[160];
    rc = gbb_cases_parse(bytes, length, &list, err, sizeof(err));
    free(bytes);
    if (rc != 0) {
        fprintf(stderr, "%s\n", rc == 1 ? err : "invalid-cases: allocation-failed line=0");
        return EXIT_INVALID;
    }
    const gbb_case *c = gbb_cases_find(&list, case_id);
    int code;
    if (c == NULL) {
        fprintf(stderr, "unknown-case: %s\n", case_id);
        code = EXIT_INVALID;
    } else {
        code = gbb_acceptance_run_case(c, options);
    }
    gbb_cases_free(&list);
    return code;
}
