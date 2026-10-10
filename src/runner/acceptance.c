#include "acceptance.h"
#include "gbb_accept.h"

#include "gabbaboy/gabbaboy.h"

#include <stdarg.h>
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
#define EXIT_EXCLUDED 4
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

/* ---- Checkpoint, rolling-digest and PCM capture (D-16, D-24, D-25) ----
 * Everything below hangs off the two gbb_accept_drive callbacks, so frames are
 * observed exactly once per completed frame and per-process state lives in one
 * heap-allocated run_state (no globals: parallel CTests never share anything). */

#define MAX_CHECKPOINTS 8u
#define FRAME_RING 3u
#define FRAME_PITCH GBB_ACCEPT_FRAME_WIDTH
#define MAX_OBSERVE_LINES 64u
#define OBSERVE_LINE_BYTES 192u
#define MAX_DIR_BYTES 3800u
/* D-25 asks for "not uniform, at least 3 distinct shades". The pinned Libbet title screen is
 * 1-bit text (shades 0 and 255 only, observed in Plan 07-07) and play_start is a 2-shade
 * transition frame, so 3 shades is only demanded of the gameplay checkpoints (mid, hit); every
 * other checkpoint must still be non-uniform (at least 2). */
#define MIN_CHECKPOINT_SHADES_GAMEPLAY 3u
#define MIN_CHECKPOINT_SHADES_SCREEN 2u

typedef struct {
    char label[GBB_ACCEPT_SCRIPT_MAX_LABEL + 1u];
    uint64_t requested_half_dots;
    bool armed;      /* requested time is known */
    bool resolved;   /* a completed frame at or after the requested time was captured */
    uint64_t completion_half_dots;
    char digest[65];
    unsigned distinct_shades;
} checkpoint;

typedef struct {
    uint64_t completion_half_dots;
    char digest[65];
    unsigned distinct_shades;
    uint8_t pixels[GBB_ACCEPT_FRAME_SHADE_BYTES];
} frame_record;

typedef struct {
    const char *id;
    const char *dump_dir;
    checkpoint checkpoints[MAX_CHECKPOINTS];
    size_t checkpoint_count;
    size_t hit_index;
    frame_record ring[FRAME_RING];   /* the newest frames, oldest overwritten */
    uint64_t frames_seen;
    uint64_t last_generation;
    uint8_t scratch[GBB_ACCEPT_FRAME_SHADE_BYTES];
    gbb_accept_sha256_ctx rolling;
    gbb_accept_track track;
    gbb_accept_pcm_digest_ctx pcm;
    gbb_accept_pcm_stats window;
    bool has_play_start;
    uint64_t play_start_half_dots;
    bool window_active;
    const char *error;               /* frame-skipped or frame-invalid: exit 3 */
    bool dump_failed;
    char final_state[96];            /* final predicate variables, printed on every non-pass line */
} run_state;

static const frame_record *newest_frame(const run_state *st) {
    return st->frames_seen == 0 ? NULL : &st->ring[(st->frames_seen - 1u) % FRAME_RING];
}

static void bin_to_hex(const uint8_t bin[32], char out[65]) {
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < 32u; ++i) {
        out[i * 2u] = digits[bin[i] >> 4];
        out[i * 2u + 1u] = digits[bin[i] & 0x0Fu];
    }
    out[64] = '\0';
}

static int join_path(char *out, size_t capacity, const char *dir, const char *name) {
    int n = snprintf(out, capacity, "%s/%s", dir, name);
    return n > 0 && (size_t)n < capacity;
}

static void resolve_checkpoint(run_state *st, checkpoint *cp, const frame_record *frame) {
    cp->resolved = true;
    cp->completion_half_dots = frame->completion_half_dots;
    memcpy(cp->digest, frame->digest, sizeof(cp->digest));
    cp->distinct_shades = frame->distinct_shades;
    if (st->dump_dir != NULL) {
        char name[128], path[MAX_DIR_BYTES + 128u];
        snprintf(name, sizeof(name), "%s.%s.ppm", st->id, cp->label);
        if (!join_path(path, sizeof(path), st->dump_dir, name) ||
            gbb_accept_write_ppm(path, frame->pixels, FRAME_PITCH) != 0) {
            st->dump_failed = true;
        }
    }
}

static void on_pcm(void *context, const gbb_audio_frame *frames, size_t count) {
    run_state *st = context;
    gbb_accept_pcm_digest_feed(&st->pcm, frames, count);
    if (st->window_active) gbb_accept_pcm_stats_feed(&st->window, frames, count);
}

static void on_after_step(void *context, gbb_instance *instance, uint64_t actual_half_dots) {
    run_state *st = context;
    /* The PCM window holds the stepping calls that start at or after play_start. */
    st->window_active = st->has_play_start && actual_half_dots >= st->play_start_half_dots;
    if (st->error != NULL) return;
    gbb_frame_info info;
    if (gbb_copy_frame(instance, st->scratch, sizeof(st->scratch), FRAME_PITCH, &info) != GBB_OK) {
        return; /* no completed frame yet (or since reset) */
    }
    if (info.generation == st->last_generation) return;
    if (info.generation != st->last_generation + 1u) {
        st->error = "frame-skipped"; /* more than one frame completed between observations */
        return;
    }
    uint8_t bin[32];
    if (gbb_accept_rgb_digest_bin(st->scratch, FRAME_PITCH, bin) != 0) {
        st->error = "frame-invalid";
        return;
    }
    st->last_generation = info.generation;
    frame_record *slot = &st->ring[st->frames_seen % FRAME_RING];
    memcpy(slot->pixels, st->scratch, sizeof(slot->pixels));
    slot->completion_half_dots = info.completion_half_dots;
    bin_to_hex(bin, slot->digest);
    slot->distinct_shades = gbb_accept_frame_distinct_shades(slot->pixels, FRAME_PITCH);
    gbb_accept_sha256_update(&st->rolling, bin, sizeof(bin));
    st->frames_seen++;
    for (size_t i = 0; i < st->checkpoint_count; ++i) {
        checkpoint *cp = &st->checkpoints[i];
        if (cp->armed && !cp->resolved && cp->requested_half_dots <= slot->completion_half_dots) {
            resolve_checkpoint(st, cp, slot);
        }
    }
}

static void on_boundary(void *context, gbb_instance *instance, uint64_t boundary_half_dots,
                        bool predicate_value) {
    (void)instance;
    run_state *st = context;
    if (st->error != NULL) return;
    bool was_hit = st->track.hit;
    gbb_accept_predicate_track(&st->track, boundary_half_dots, predicate_value);
    if (was_hit || !st->track.hit) return;
    /* T_hit is only known one boundary late, so the hit frame is the earliest recent frame that
     * completed at or after T_hit; later frames resolve it in on_after_step if none has yet. */
    checkpoint *cp = &st->checkpoints[st->hit_index];
    cp->requested_half_dots = st->track.t_hit;
    cp->armed = true;
    uint64_t held = st->frames_seen < FRAME_RING ? st->frames_seen : FRAME_RING;
    for (uint64_t k = held; k > 0; --k) {
        const frame_record *frame = &st->ring[(st->frames_seen - k) % FRAME_RING];
        if (frame->completion_half_dots >= cp->requested_half_dots) {
            resolve_checkpoint(st, cp, frame);
            break;
        }
    }
}

static void add_checkpoint(run_state *st, const char *label, uint64_t requested, bool armed) {
    checkpoint *cp = &st->checkpoints[st->checkpoint_count++];
    memset(cp, 0, sizeof(*cp));
    strcpy(cp->label, label);
    cp->requested_half_dots = requested;
    cp->armed = armed;
}

static const gbb_accept_mark *find_mark(const gbb_accept_script *script, const char *label) {
    for (size_t i = 0; i < script->mark_count; ++i) {
        if (strcmp(script->marks[i].label, label) == 0) return &script->marks[i];
    }
    return NULL;
}

/* Writes and removes a probe file so an unwritable directory is found before any guest work. */
static int probe_directory(const char *dir) {
    char path[MAX_DIR_BYTES + 32u];
    if (strlen(dir) > MAX_DIR_BYTES || !join_path(path, sizeof(path), dir, ".gbb-write-probe")) return 0;
    FILE *file = fopen(path, "wb");
    if (file == NULL) return 0;
    int ok = fclose(file) == 0;
    remove(path);
    return ok;
}

static unsigned min_shades_for(const char *label) {
    return strcmp(label, "mid") == 0 || strcmp(label, "hit") == 0 ? MIN_CHECKPOINT_SHADES_GAMEPLAY
                                                                  : MIN_CHECKPOINT_SHADES_SCREEN;
}

static int pcm_has_samples(const run_state *st) {
    return st->window.samples != 0;
}

typedef struct {
    char lines[MAX_OBSERVE_LINES][OBSERVE_LINE_BYTES];
    size_t count;
} observe_lines;

static void emit_line(observe_lines *out, const char *id, const char *suffix, const char *fmt, ...) {
    if (out->count >= MAX_OBSERVE_LINES) return;
    char value[96];
    va_list args;
    va_start(args, fmt);
    vsnprintf(value, sizeof(value), fmt, args);
    va_end(args);
    snprintf(out->lines[out->count++], OBSERVE_LINE_BYTES, "acceptance.%s.%s\t%s", id, suffix, value);
}

static int compare_lines(const void *a, const void *b) {
    return strcmp((const char *)a, (const char *)b);
}

static void print_observation(const gbb_case *c, const run_state *st, bool hit, uint64_t t_hit,
                              bool pcm_only, const char pcm_hex[65], const char rolling_hex[65]) {
    observe_lines *out = malloc(sizeof(*out));
    if (out == NULL) {
        fprintf(stderr, "runner-error: observation allocation failed\n");
        return;
    }
    out->count = 0;
    char key[96];
    if (!pcm_only) {
        emit_line(out, c->id, "class", "regression");
        if (hit) emit_line(out, c->id, "t_hit_half_dots", "%llu", (unsigned long long)t_hit);
        else emit_line(out, c->id, "t_hit_half_dots", "none");
        for (size_t i = 0; i < st->checkpoint_count; ++i) {
            const checkpoint *cp = &st->checkpoints[i];
            snprintf(key, sizeof(key), "checkpoint.%s.requested_half_dots", cp->label);
            if (cp->armed) emit_line(out, c->id, key, "%llu", (unsigned long long)cp->requested_half_dots);
            else emit_line(out, c->id, key, "none");
            snprintf(key, sizeof(key), "checkpoint.%s.completion_half_dots", cp->label);
            if (cp->resolved) emit_line(out, c->id, key, "%llu", (unsigned long long)cp->completion_half_dots);
            else emit_line(out, c->id, key, "none");
            snprintf(key, sizeof(key), "checkpoint.%s.frame", cp->label);
            emit_line(out, c->id, key, "%s", cp->resolved ? cp->digest : "none");
        }
        emit_line(out, c->id, "frame.rolling", "%s", rolling_hex);
    }
    emit_line(out, c->id, "pcm_sha256", "%s", pcm_hex);
    emit_line(out, c->id, "pcm.window.left.peak_to_peak", "%d",
              (int)gbb_accept_pcm_peak_to_peak(&st->window.left, st->window.samples));
    emit_line(out, c->id, "pcm.window.left.changes", "%llu", (unsigned long long)st->window.left.changes);
    emit_line(out, c->id, "pcm.window.right.peak_to_peak", "%d",
              (int)gbb_accept_pcm_peak_to_peak(&st->window.right, st->window.samples));
    emit_line(out, c->id, "pcm.window.right.changes", "%llu", (unsigned long long)st->window.right.changes);
    qsort(out->lines, out->count, OBSERVE_LINE_BYTES, compare_lines);
    for (size_t i = 0; i < out->count; ++i) printf("%s\n", out->lines[i]);
    free(out);
}

/* Receipt tokens that mark a control run (D-14): the raw verdict and any event mutation. */
static void run_note(const gbb_acceptance_options *options, char out[64]) {
    out[0] = '\0';
    size_t used = 0;
    if (options == NULL) return;
    if (options->has_drop_button && options->mutate_label != NULL) {
        int n = snprintf(out, 64, " mutate=%s", options->mutate_label);
        used = n > 0 && n < 64 ? (size_t)n : 0;
    }
    if (options->raw_verdict) snprintf(out + used, 64 - used, " raw_verdict=1");
}

static int fail_run(const gbb_case *c, const gbb_acceptance_options *options, const run_state *st,
                    const char *reason, uint64_t end_half_dots) {
    char ppm_note[MAX_DIR_BYTES + 160u], note[64], final_note[112];
    ppm_note[0] = '\0';
    run_note(options, note);
    final_note[0] = '\0';
    if (st->final_state[0] != '\0') snprintf(final_note, sizeof(final_note), " %s", st->final_state);
    const frame_record *frame = newest_frame(st);
    if (options != NULL && options->failure_dir != NULL && frame != NULL) {
        char name[96], path[MAX_DIR_BYTES + 128u];
        snprintf(name, sizeof(name), "%s.ppm", c->id);
        if (join_path(path, sizeof(path), options->failure_dir, name) &&
            gbb_accept_write_ppm(path, frame->pixels, FRAME_PITCH) == 0) {
            snprintf(ppm_note, sizeof(ppm_note), " ppm=%s", path);
        } else {
            snprintf(ppm_note, sizeof(ppm_note), " ppm=write-failed");
        }
    }
    if (options != NULL && options->expect_fail && options->expect_fail_reason != NULL &&
        options->expect_fail_reason[0] != '\0' && strcmp(options->expect_fail_reason, reason) == 0) {
        /* Strict expected failure (D-22): only the declared reason counts, and it counts as xfail. */
        printf("acceptance id=%s status=xfail model=dmg-cpu-b reason=%s end_half_dots=%llu%s%s\n", c->id, reason,
               (unsigned long long)end_half_dots, final_note, note);
        if (options->xfailed != NULL) *options->xfailed = 1;
        return EXIT_PASS;
    }
    printf("acceptance id=%s status=fail model=dmg-cpu-b reason=%s end_half_dots=%llu%s%s%s\n", c->id, reason,
           (unsigned long long)end_half_dots, final_note, note, ppm_note);
    return EXIT_FAIL;
}

/* ---- LD B,B and timed frame capture (EVID-01, D-24) ---- */

#define CAPTURE_CHUNK UINT64_C(2048)
#define CAPTURE_TRACE 128u

_Static_assert(GBB_LDBB_FRAME_BYTES == GBB_ACCEPT_FRAME_SHADE_BYTES, "frame buffer size");

typedef struct {
    uint8_t pixels[GBB_LDBB_FRAME_BYTES];
    gbb_frame_info info;
} scratch_frame;

/* A chunk is at most 2048 half-dots and a frame lasts 140448, so at most one frame completes per
 * chunk and "latest frame at or before time T" needs only the frame held before the chunk and the
 * one seen after it. */
static int copy_latest(gbb_instance *instance, scratch_frame *frame) {
    return gbb_copy_frame(instance, frame->pixels, sizeof(frame->pixels), FRAME_PITCH, &frame->info) == GBB_OK;
}

static int finish_capture(gbb_ldbb_capture *out) {
    if (!out->frame_ready) return 0;
    return gbb_accept_rgb_digest(out->pixels, FRAME_PITCH, out->digest) == 0 ? 0 : 2;
}

int gbb_runner_capture_ldbb(gbb_instance *instance, uint64_t budget_half_dots, gbb_ldbb_capture *out) {
    memset(out, 0, sizeof(*out));
    scratch_frame *next = malloc(sizeof(*next));
    gbb_trace_record *trace = malloc(CAPTURE_TRACE * sizeof(*trace));
    if (next == NULL || trace == NULL) {
        free(next);
        free(trace);
        return 1;
    }
    uint64_t elapsed = 0, held_generation = 0;
    while (elapsed < budget_half_dots) {
        uint64_t slice = budget_half_dots - elapsed < CAPTURE_CHUNK ? budget_half_dots - elapsed : CAPTURE_CHUNK;
        gbb_run_result r = gbb_run(instance, slice, trace, CAPTURE_TRACE);
        elapsed += r.consumed_half_dots;
        const gbb_trace_record *hit = NULL;
        for (size_t i = 0; i < r.trace_count && hit == NULL; ++i) {
            if (trace[i].opcode[0] == 0x40u) hit = &trace[i];
        }
        bool fresh = copy_latest(instance, next) && (!out->frame_ready || next->info.generation != held_generation);
        if (hit != NULL) {
            if (fresh && next->info.completion_half_dots <= hit->time_half_dots) {
                memcpy(out->pixels, next->pixels, sizeof(out->pixels));
                out->frame_ready = 1;
                out->completion_half_dots = next->info.completion_half_dots;
                out->generation = next->info.generation;
            }
            out->reached = 1;
            out->ldbb_half_dots = hit->time_half_dots;
            out->pc = hit->pc;
            out->b = hit->b; out->c = hit->c; out->d = hit->d;
            out->e = hit->e; out->h = hit->h; out->l = hit->l;
            break;
        }
        if (fresh) {
            memcpy(out->pixels, next->pixels, sizeof(out->pixels));
            out->frame_ready = 1;
            out->completion_half_dots = next->info.completion_half_dots;
            out->generation = held_generation = next->info.generation;
        }
        if (r.consumed_half_dots == 0) break;
        if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_TRACE_FULL && r.reason != GBB_STOP_HALTED_IDLE) break;
    }
    free(next);
    free(trace);
    return finish_capture(out);
}

/* frame-digest@t=<n>: the first frame whose completion is at or after n. */
static int capture_frame_at(gbb_instance *instance, uint64_t at_half_dots, uint64_t budget_half_dots,
                            gbb_ldbb_capture *out) {
    memset(out, 0, sizeof(*out));
    scratch_frame *next = malloc(sizeof(*next));
    if (next == NULL) return 1;
    uint64_t elapsed = 0, seen_generation = 0;
    bool seen = false;
    while (elapsed < budget_half_dots && !out->frame_ready) {
        uint64_t slice = budget_half_dots - elapsed < CAPTURE_CHUNK ? budget_half_dots - elapsed : CAPTURE_CHUNK;
        gbb_run_result r = gbb_run(instance, slice, NULL, 0);
        elapsed += r.consumed_half_dots;
        if (copy_latest(instance, next) && (!seen || next->info.generation != seen_generation)) {
            seen = true;
            seen_generation = next->info.generation;
            if (next->info.completion_half_dots >= at_half_dots) {
                memcpy(out->pixels, next->pixels, sizeof(out->pixels));
                out->frame_ready = 1;
                out->completion_half_dots = next->info.completion_half_dots;
                out->generation = next->info.generation;
            }
        }
        if (r.consumed_half_dots == 0) break;
        if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_HALTED_IDLE) break;
    }
    free(next);
    return finish_capture(out);
}

/* Frame-digest verdicts (D-26): every one is class=regression, because no frame-digest case has an
 * independent oracle this phase. An expected failure (model_fail) counts only for its declared reason. */
static int frame_fail(const gbb_case *c, const gbb_acceptance_options *options, const char *reason,
                      const char *observed, uint64_t end_half_dots, const uint8_t *pixels) {
    if (options != NULL && options->expect_fail && options->expect_fail_reason != NULL &&
        strcmp(options->expect_fail_reason, reason) == 0) {
        printf("acceptance id=%s status=xfail model=dmg-cpu-b reason=%s class=regression end_half_dots=%llu\n", c->id,
               reason, (unsigned long long)end_half_dots);
        if (options->xfailed != NULL) *options->xfailed = 1;
        return EXIT_PASS;
    }
    char observed_note[96], ppm_note[MAX_DIR_BYTES + 160u];
    observed_note[0] = ppm_note[0] = '\0';
    if (observed != NULL) snprintf(observed_note, sizeof(observed_note), " observed=%s", observed);
    if (options != NULL && options->failure_dir != NULL && pixels != NULL) {
        char name[96], path[MAX_DIR_BYTES + 128u];
        snprintf(name, sizeof(name), "%s.ppm", c->id);
        if (join_path(path, sizeof(path), options->failure_dir, name) &&
            gbb_accept_write_ppm(path, pixels, FRAME_PITCH) == 0) {
            snprintf(ppm_note, sizeof(ppm_note), " ppm=%s", path);
        } else {
            snprintf(ppm_note, sizeof(ppm_note), " ppm=write-failed");
        }
    }
    printf("acceptance id=%s status=fail model=dmg-cpu-b reason=%s class=regression%s end_half_dots=%llu%s\n", c->id,
           reason, observed_note, (unsigned long long)end_half_dots, ppm_note);
    return EXIT_FAIL;
}

static int run_frame_case(const gbb_case *c, const gbb_acceptance_options *options) {
    const bool observe = options != NULL && options->observe;
    uint8_t *rom = NULL;
    size_t rom_length = 0;
    gbb_instance *instance = NULL;
    gbb_ldbb_capture *capture = NULL;
    char digest[65];
    int code = EXIT_INVALID;

    if (options != NULL && (options->observe_input_script != NULL || options->has_frame_digest_at || options->pcm_only)) {
        return input_error(c, "observe-flag-not-applicable");
    }
    int rc = gbb_runner_read_file(c->rom, GBB_CASES_MAX_ROM_BYTES, &rom, &rom_length);
    if (rc != 0) { code = input_error(c, rc == 1 ? "rom-missing" : "rom-unreadable"); goto done; }
    if (rom_length != c->rom_size) { code = input_error(c, "rom-size-mismatch"); goto done; }
    gbb_accept_sha256_hex(rom, rom_length, digest);
    if (strcmp(digest, c->rom_sha256) != 0) { code = input_error(c, "rom-digest-mismatch"); goto done; }
    if (options != NULL && options->failure_dir != NULL && !probe_directory(options->failure_dir)) {
        code = input_error(c, "failure-dir-unwritable");
        goto done;
    }
    const char *dump_dir = observe ? options->dump_dir : NULL;
    if (dump_dir != NULL && !probe_directory(dump_dir)) { code = input_error(c, "dump-dir-unwritable"); goto done; }

    capture = malloc(sizeof(*capture));
    if (capture == NULL || gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) != GBB_OK) {
        fprintf(stderr, "runner-error: instance allocation failed\n");
        goto done;
    }
    if (gbb_load_rom(instance, rom, rom_length) != GBB_OK) { code = input_error(c, "rom-rejected"); goto done; }

    const bool at_ldbb = c->oracle == GBB_ORACLE_FRAME_DIGEST_LDBB;
    rc = at_ldbb ? gbb_runner_capture_ldbb(instance, c->budget_half_dots, capture)
                 : capture_frame_at(instance, c->oracle_half_dots, c->budget_half_dots, capture);
    if (rc != 0) {
        printf("acceptance id=%s status=unsupported model=dmg-cpu-b reason=%s\n", c->id,
               rc == 1 ? "capture-allocation" : "frame-invalid");
        code = EXIT_UNSUPPORTED;
        goto done;
    }
    char label[48];
    if (at_ldbb) snprintf(label, sizeof(label), "ldbb");
    else snprintf(label, sizeof(label), "t%llu", (unsigned long long)c->oracle_half_dots);

    if (observe) {
        if (dump_dir != NULL && capture->frame_ready) {
            char name[128], path[MAX_DIR_BYTES + 128u];
            snprintf(name, sizeof(name), "%s.%s.ppm", c->id, label);
            if (!join_path(path, sizeof(path), dump_dir, name) ||
                gbb_accept_write_ppm(path, capture->pixels, FRAME_PITCH) != 0) {
                fprintf(stderr, "acceptance id=%s status=invalid reason=dump-write-failed\n", c->id);
                goto done;
            }
        }
        observe_lines *out = malloc(sizeof(*out));
        if (out == NULL) {
            fprintf(stderr, "runner-error: observation allocation failed\n");
            goto done;
        }
        out->count = 0;
        char key[96];
        emit_line(out, c->id, "class", "regression");
        if (at_ldbb) {
            if (capture->reached) emit_line(out, c->id, "ldbb_half_dots", "%llu", (unsigned long long)capture->ldbb_half_dots);
            else emit_line(out, c->id, "ldbb_half_dots", "none");
        }
        snprintf(key, sizeof(key), "checkpoint.%s.completion_half_dots", label);
        if (capture->frame_ready) emit_line(out, c->id, key, "%llu", (unsigned long long)capture->completion_half_dots);
        else emit_line(out, c->id, key, "none");
        snprintf(key, sizeof(key), "checkpoint.%s.frame", label);
        emit_line(out, c->id, key, "%s", capture->frame_ready ? capture->digest : "none");
        qsort(out->lines, out->count, OBSERVE_LINE_BYTES, compare_lines);
        for (size_t i = 0; i < out->count; ++i) printf("%s\n", out->lines[i]);
        free(out);
        code = EXIT_PASS;
        goto done;
    }

    if (at_ldbb && !capture->reached) {
        code = frame_fail(c, options, "ldbb-not-reached", NULL, c->budget_half_dots, NULL);
    } else if (!capture->frame_ready) {
        code = frame_fail(c, options, "frame-not-ready", NULL, at_ldbb ? capture->ldbb_half_dots : c->budget_half_dots, NULL);
    } else if (strcmp(capture->digest, c->reference_digest) != 0) {
        code = frame_fail(c, options, "frame-mismatch", capture->digest, capture->completion_half_dots, capture->pixels);
    } else if (options != NULL && options->expect_fail) {
        printf("acceptance id=%s status=unexpected-pass model=dmg-cpu-b class=regression\n", c->id);
        code = EXIT_FAIL;
    } else {
        printf("acceptance id=%s status=pass model=dmg-cpu-b class=regression end_half_dots=%llu\n", c->id,
               (unsigned long long)capture->completion_half_dots);
        code = EXIT_PASS;
    }

done:
    gbb_destroy(instance);
    free(capture);
    free(rom);
    return code;
}

int gbb_acceptance_run_case(const gbb_case *c, const gbb_acceptance_options *options) {
    uint8_t *script_bytes = NULL, *rom = NULL;
    size_t script_length = 0, rom_length = 0;
    gbb_accept_script script;
    gbb_accept_stepper *stepper = NULL;
    gbb_instance *instance = NULL;
    run_state *st = NULL;
    char digest[65], err[160];
    int code = EXIT_INVALID;
    const bool observe = options != NULL && options->observe;
    memset(&script, 0, sizeof(script));

    if (c->oracle != GBB_ORACLE_PROGRESS_PREDICATE) return run_frame_case(c, options);

    /* Input script: digest over the raw bytes first, then syntax. Under --observe only, an explicit
     * script replaces the case script and is not digest-pinned (it can never produce a pass). */
    const bool replaced = observe && options->observe_input_script != NULL;
    int rc = gbb_runner_read_file(replaced ? options->observe_input_script : c->input_script,
                                  GBB_ACCEPT_SCRIPT_MAX_BYTES, &script_bytes, &script_length);
    if (rc != 0) { code = input_error(c, rc == 1 ? "input-missing" : "input-unreadable"); goto done; }
    if (!replaced) {
        gbb_accept_sha256_hex(script_bytes, script_length, digest);
        if (strcmp(digest, c->input_sha256) != 0) { code = input_error(c, "input-digest-mismatch"); goto done; }
    }
    rc = gbb_accept_script_parse(script_bytes, script_length, &script, err, sizeof(err));
    if (rc != 0) {
        fprintf(stderr, "acceptance id=%s status=invalid reason=invalid-script detail=\"%s\"\n", c->id, rc == 1 ? err : "allocation");
        goto done;
    }

    /* D-14 mutation: remove one button's events after the script is validated, so a bad script is
     * still rejected first. Order is preserved, so the stream stays nondecreasing. */
    if (options != NULL && options->has_drop_button) {
        size_t kept = 0;
        for (size_t i = 0; i < script.event_count; ++i) {
            const gbb_input_event *event = &script.events[i];
            bool button_event = event->kind == GBB_INPUT_BUTTON_PRESS || event->kind == GBB_INPUT_BUTTON_RELEASE;
            if (button_event && event->value == options->drop_button) continue;
            script.events[kept++] = *event;
        }
        script.event_count = kept;
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

    /* Checkpoint plan (D-25): the script marks title, play_start and mid, then the hit frame. A
     * run that is gated needs all three marks; --observe records whichever exist. */
    static const char *const mark_labels[] = {"title", "play_start", "mid"};
    st = calloc(1, sizeof(*st));
    if (st == NULL) {
        fprintf(stderr, "runner-error: run state allocation failed\n");
        goto done;
    }
    st->id = c->id;
    st->dump_dir = observe ? options->dump_dir : NULL;
    for (size_t i = 0; i < sizeof(mark_labels) / sizeof(mark_labels[0]); ++i) {
        const gbb_accept_mark *mark = find_mark(&script, mark_labels[i]);
        if (mark == NULL) {
            if (observe) continue;
            code = input_error(c, "checkpoint-mark-missing");
            goto done;
        }
        add_checkpoint(st, mark_labels[i], mark->at_half_dots, true);
        if (strcmp(mark_labels[i], "play_start") == 0) {
            st->has_play_start = true;
            st->play_start_half_dots = mark->at_half_dots;
        }
    }
    if (observe && options->has_frame_digest_at) {
        char label[GBB_ACCEPT_SCRIPT_MAX_LABEL + 1u];
        snprintf(label, sizeof(label), "t%llu", (unsigned long long)options->frame_digest_at);
        if (find_mark(&script, label) != NULL) { code = input_error(c, "checkpoint-label-duplicate"); goto done; }
        add_checkpoint(st, label, options->frame_digest_at, true);
    }
    add_checkpoint(st, "hit", 0, false);
    st->hit_index = st->checkpoint_count - 1u;
    gbb_accept_sha256_init(&st->rolling);
    gbb_accept_pcm_digest_init(&st->pcm);
    gbb_accept_pcm_stats_init(&st->window);
    gbb_accept_track_init(&st->track);

    /* Output directories are probed before any guest work (T-07-16). */
    if (options != NULL && options->failure_dir != NULL && !probe_directory(options->failure_dir)) {
        code = input_error(c, "failure-dir-unwritable");
        goto done;
    }
    if (st->dump_dir != NULL && !probe_directory(st->dump_dir)) {
        code = input_error(c, "dump-dir-unwritable");
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
    gbb_accept_stepper_init(stepper, instance, on_pcm, st);

    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = stepper;
    config.script = &script;
    config.predicate = predicate;
    config.expect_hw = c->expect_hw_capability;
    config.budget_half_dots = c->budget_half_dots;
    config.tail_half_dots = GBB_ACCEPT_TAIL_HALF_DOTS; /* the D-16 PCM window ends 1 s after T_hit */
    config.max_batch = DRIVE_MAX_BATCH;
    config.after_step = on_after_step;
    config.at_boundary = on_boundary;
    config.context = st;
    gbb_accept_drive_result result;
    gbb_accept_drive(&config, &result);

    /* Final predicate variables (D-14): what the guest actually reached, so a control's failure is
     * explained by state rather than by absence. Two-digit hex per byte. */
#define FINAL(role) gbb_peek_ram(instance, predicate->rows[role].address)
    snprintf(st->final_state, sizeof(st->final_state),
             "final_hw=%02x final_attract=%02x final_floor=%02x final_score=%02x/%02x final_size=%02xx%02x",
             FINAL(GBB_ACCEPT_ROLE_HW_CAPABILITY), FINAL(GBB_ACCEPT_ROLE_ATTRACT_MODE),
             FINAL(GBB_ACCEPT_ROLE_CUR_FLOOR), FINAL(GBB_ACCEPT_ROLE_CUR_SCORE),
             FINAL(GBB_ACCEPT_ROLE_MAX_SCORE), FINAL(GBB_ACCEPT_ROLE_FLOOR_WIDTH),
             FINAL(GBB_ACCEPT_ROLE_FLOOR_HEIGHT));
#undef FINAL

    char pcm_hex[65], rolling_hex[65];
    gbb_accept_pcm_digest_final(&st->pcm, pcm_hex);
    gbb_accept_sha256_final(&st->rolling, rolling_hex);

    if (st->error != NULL) {
        printf("acceptance id=%s status=unsupported model=dmg-cpu-b reason=%s end_half_dots=%llu\n", c->id,
               st->error, (unsigned long long)result.end_half_dots);
        code = EXIT_UNSUPPORTED;
        goto done;
    }
    if (st->dump_failed) {
        fprintf(stderr, "acceptance id=%s status=invalid reason=dump-write-failed\n", c->id);
        code = EXIT_INVALID;
        goto done;
    }

    if (observe && (result.status == GBB_ACCEPT_DRIVE_HIT || result.status == GBB_ACCEPT_DRIVE_NOT_REACHED)) {
        print_observation(c, st, result.status == GBB_ACCEPT_DRIVE_HIT, result.t_hit_half_dots,
                          options->pcm_only, pcm_hex, rolling_hex);
        code = EXIT_PASS;
        goto done;
    }

    switch (result.status) {
    case GBB_ACCEPT_DRIVE_HIT: {
        /* Evidence gates (D-16, D-25): every checkpoint frame exists and is structured, the hit
         * differs from the title, and both channels are audible in the play window. */
        const char *reason = NULL;
        for (size_t i = 0; i < st->checkpoint_count && reason == NULL; ++i) {
            if (!st->checkpoints[i].resolved) reason = "checkpoint-not-ready";
        }
        for (size_t i = 0; i < st->checkpoint_count && reason == NULL; ++i) {
            if (st->checkpoints[i].distinct_shades < min_shades_for(st->checkpoints[i].label)) {
                reason = "checkpoint-structure";
            }
        }
        if (reason == NULL && strcmp(st->checkpoints[0].digest, st->checkpoints[st->hit_index].digest) == 0) {
            reason = "checkpoint-structure";
        }
        if (reason == NULL && (!pcm_has_samples(st) || !gbb_accept_pcm_audible(&st->window))) reason = "pcm-silent";
        if (reason != NULL) {
            code = fail_run(c, options, st, reason, result.end_half_dots);
            break;
        }
        char note[64];
        run_note(options, note);
        if (options != NULL && options->expect_fail) {
            /* model_fail is strict: a case that was expected to fail and passed is a failure. */
            printf("acceptance id=%s status=unexpected-pass model=dmg-cpu-b t_hit_half_dots=%llu%s\n", c->id,
                   (unsigned long long)result.t_hit_half_dots, note);
            code = EXIT_FAIL;
            break;
        }
        printf("acceptance id=%s status=pass model=dmg-cpu-b t_hit_half_dots=%llu%s\n", c->id,
               (unsigned long long)result.t_hit_half_dots, note);
        if (options != NULL && options->receipt) {
            printf("receipt id=%s rom_sha256=%s rom_size=%u input_sha256=%s predicate=%s "
                   "budget_half_dots=%llu end_half_dots=%llu core_revision=%s build_qualified=%s",
                   c->id, c->rom_sha256, (unsigned)c->rom_size, c->input_sha256, c->predicate,
                   (unsigned long long)c->budget_half_dots,
                   (unsigned long long)result.end_half_dots,
                   options->core_revision != NULL ? options->core_revision : "unknown",
                   options->build_qualified ? "true" : "false");
            for (size_t i = 0; i < st->checkpoint_count; ++i) {
                printf(" frame_%s=%s", st->checkpoints[i].label, st->checkpoints[i].digest);
            }
            printf(" frame_rolling=%s pcm_sha256=%s pcm_left_peak_to_peak=%d pcm_left_changes=%llu "
                   "pcm_right_peak_to_peak=%d pcm_right_changes=%llu\n",
                   rolling_hex, pcm_hex,
                   (int)gbb_accept_pcm_peak_to_peak(&st->window.left, st->window.samples),
                   (unsigned long long)st->window.left.changes,
                   (int)gbb_accept_pcm_peak_to_peak(&st->window.right, st->window.samples),
                   (unsigned long long)st->window.right.changes);
        }
        code = EXIT_PASS;
        break;
    }
    case GBB_ACCEPT_DRIVE_NOT_REACHED:
        code = fail_run(c, options, st, "predicate-not-reached", result.end_half_dots);
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
    free(st);
    free(rom);
    free(script_bytes);
    return code;
}

/* Applies D-22 applicability, then runs the case with the expected-failure fields filled in. An
 * excluded case exits 4 without creating an instance; only dmg-cpu-b can execute in this phase. */
static int run_applicable(const gbb_case *c, const gbb_acceptance_options *options, int *excluded,
                          int *xfailed) {
    const char *model = options->model != NULL ? options->model : "dmg-cpu-b";
    *excluded = 0;
    *xfailed = 0;
    gbb_case_applicability_kind kind = gbb_case_applicability(c, model, options->revision);
    if (kind == GBB_CASE_EXCLUDED_MODEL || kind == GBB_CASE_EXCLUDED_REVISION) {
        printf("acceptance id=%s status=excluded reason=%s model=%s\n", c->id,
               kind == GBB_CASE_EXCLUDED_MODEL ? "unsupported-model" : "target-revision", model);
        *excluded = 1;
        return EXIT_EXCLUDED;
    }
    if (strcmp(model, "dmg-cpu-b") != 0) {
        printf("acceptance id=%s status=unsupported reason=unsupported-profile model=%s\n", c->id, model);
        return EXIT_UNSUPPORTED;
    }
    gbb_acceptance_options run = *options;
    run.expect_fail = kind == GBB_CASE_EXPECT_FAIL && !options->raw_verdict;
    run.expect_fail_reason = c->expect_fail_reason;
    run.xfailed = xfailed;
    return gbb_acceptance_run_case(c, &run);
}

/* Runs every case in file order. The suite passes only when something was eligible, every eligible
 * case ran and passed or failed as declared, and the excluded count equals the declared count, so
 * moving a case to excluded cannot shrink the denominator silently. */
static int run_suite(const gbb_case_list *list, const gbb_acceptance_options *options) {
    size_t eligible = 0, executed = 0, excluded = 0, xfail = 0;
    int first_code = 0;
    for (size_t i = 0; i < list->count; ++i) {
        int was_excluded = 0, xfailed = 0;
        int code = run_applicable(&list->cases[i], options, &was_excluded, &xfailed);
        if (was_excluded) {
            excluded++;
            continue;
        }
        eligible++;
        if (code == EXIT_PASS || code == EXIT_FAIL) executed++;
        if (xfailed) xfail++;
        if (code != EXIT_PASS && first_code == 0) first_code = code;
    }
    const char *reason = NULL;
    char detail[96];
    detail[0] = '\0';
    int code = EXIT_PASS;
    if (eligible == 0) {
        reason = "no-eligible-cases";
        code = EXIT_FAIL;
    } else if (excluded != options->expect_excluded) {
        reason = "excluded-count-mismatch";
        snprintf(detail, sizeof(detail), " expected=%u observed=%zu", options->expect_excluded, excluded);
        code = EXIT_FAIL;
    } else if (executed != eligible || first_code != 0) {
        code = first_code != 0 ? first_code : EXIT_FAIL;
    }
    printf("suite eligible=%zu executed=%zu excluded=%zu xfail=%zu status=%s%s%s%s\n", eligible, executed,
           excluded, xfail, code == EXIT_PASS ? "pass" : "fail", reason != NULL ? " reason=" : "",
           reason != NULL ? reason : "", detail);
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
    int code;
    if (options->suite) {
        code = run_suite(&list, options);
        gbb_cases_free(&list);
        return code;
    }
    const gbb_case *c = gbb_cases_find(&list, case_id);
    if (c == NULL) {
        fprintf(stderr, "unknown-case: %s\n", case_id);
        code = EXIT_INVALID;
    } else {
        int excluded = 0, xfailed = 0;
        code = run_applicable(c, options, &excluded, &xfailed);
    }
    gbb_cases_free(&list);
    return code;
}
