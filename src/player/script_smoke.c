#include "script_smoke.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void set_message(char *err, size_t capacity, const char *text) {
    if (err != NULL && capacity > 0u) snprintf(err, capacity, "%s", text);
}

/* Bounded whole-file read: a file longer than limit is rejected, not truncated. */
static int read_bounded(const char *path, size_t limit, uint8_t **out, size_t *out_length,
                        char *err, size_t err_capacity) {
    *out = NULL;
    *out_length = 0u;
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        set_message(err, err_capacity, "could not open input file");
        return 1;
    }
    uint8_t *bytes = malloc(limit + 1u);
    if (bytes == NULL) {
        fclose(file);
        set_message(err, err_capacity, "allocation failed");
        return 1;
    }
    const size_t got = fread(bytes, 1u, limit + 1u, file);
    const bool failed = ferror(file) != 0;
    fclose(file);
    if (failed || got > limit) {
        free(bytes);
        set_message(err, err_capacity, failed ? "could not read input file" : "input file is too large");
        return 1;
    }
    *out = bytes;
    *out_length = got;
    return 0;
}

int player_script_smoke_prepare(player_script_smoke *smoke, const char *rom_path,
                                const char *script_path, char *err, size_t err_capacity) {
    memset(smoke, 0, sizeof(*smoke));
    uint8_t *script_bytes = NULL;
    size_t script_length = 0u;
    char detail[160];
    if (read_bounded(script_path, GBB_ACCEPT_SCRIPT_MAX_BYTES, &script_bytes, &script_length,
                     detail, sizeof(detail)) != 0) {
        snprintf(err, err_capacity, "input script: %s", detail);
        return 1;
    }
    const int parsed = gbb_accept_script_parse(script_bytes, script_length, &smoke->script,
                                               detail, sizeof(detail));
    free(script_bytes);
    if (parsed != 0) {
        set_message(err, err_capacity, parsed == 1 ? detail : "input script: allocation failed");
        return 1;
    }
    if (read_bounded(rom_path, PLAYER_SCRIPT_SMOKE_ROM_LIMIT, &smoke->rom, &smoke->rom_length,
                     detail, sizeof(detail)) != 0) {
        snprintf(err, err_capacity, "rom: %s", detail);
        player_script_smoke_release(smoke);
        return 1;
    }
    gbb_accept_sha256_hex(smoke->rom, smoke->rom_length, smoke->rom_sha256);
    smoke->predicate = gbb_accept_predicate_find(PLAYER_SCRIPT_SMOKE_PREDICATE, smoke->rom_sha256);
    if (smoke->predicate == NULL ||
        !gbb_accept_predicate_anchors_match(smoke->predicate, smoke->rom, smoke->rom_length)) {
        set_message(err, err_capacity, "rom: no pinned progress predicate for this ROM digest");
        player_script_smoke_release(smoke);
        return 1;
    }
    return 0;
}

void player_script_smoke_release(player_script_smoke *smoke) {
    gbb_accept_script_free(&smoke->script);
    free(smoke->rom);
    memset(smoke, 0, sizeof(*smoke));
}

typedef struct {
    const player_script_smoke *smoke;
    player_audio *audio;
    player_script_smoke_deliver_fn deliver;
    player_script_smoke_progress_fn progress;
    void *context;
    gbb_accept_pcm_digest_ctx digest;
    gbb_accept_pcm_stats window;
    bool has_play_start;
    uint64_t play_start_half_dots;
    bool window_active;
} smoke_state;

static void on_pcm(void *context, const gbb_audio_frame *frames, size_t count) {
    smoke_state *st = context;
    /* Digest and statistics first: what the session buffer receives is what is measured. */
    gbb_accept_pcm_digest_feed(&st->digest, frames, count);
    if (st->window_active) gbb_accept_pcm_stats_feed(&st->window, frames, count);
    /* The smoke runs faster than real time, so the bounded ring may refuse a batch; that is
     * counted by the audio module as backpressure and never changes the digest. */
    for (size_t offset = 0u; st->audio != NULL && offset < count;) {
        const size_t chunk = count - offset > 512u ? 512u : count - offset;
        (void)player_audio_submit(st->audio, frames + offset, (unsigned)chunk);
        offset += chunk;
    }
}

static bool on_deliver(void *context, const gbb_input_event *events, size_t count) {
    smoke_state *st = context;
    return st->deliver(st->context, events, count);
}

static void on_after_step(void *context, gbb_instance *instance, uint64_t actual_half_dots) {
    (void)instance;
    smoke_state *st = context;
    /* Same rule as the runner: the window holds stepping calls starting at or after play_start. */
    st->window_active = st->has_play_start && actual_half_dots >= st->play_start_half_dots;
    if (st->progress != NULL) st->progress(st->context, actual_half_dots);
}

bool player_script_smoke_run(const player_script_smoke *smoke, gbb_instance *instance,
                             player_audio *audio, player_script_smoke_deliver_fn deliver,
                             player_script_smoke_progress_fn progress, void *context,
                             player_script_smoke_result *result) {
    memset(result, 0, sizeof(*result));
    smoke_state *st = calloc(1u, sizeof(*st));
    gbb_accept_stepper *stepper = malloc(sizeof(*stepper)); /* carries a PCM buffer */
    if (st == NULL || stepper == NULL) {
        free(st);
        free(stepper);
        return false;
    }
    st->smoke = smoke;
    st->audio = audio;
    st->deliver = deliver;
    st->progress = progress;
    st->context = context;
    gbb_accept_pcm_digest_init(&st->digest);
    gbb_accept_pcm_stats_init(&st->window);
    for (size_t i = 0u; i < smoke->script.mark_count; ++i) {
        if (strcmp(smoke->script.marks[i].label, "play_start") == 0) {
            st->has_play_start = true;
            st->play_start_half_dots = smoke->script.marks[i].at_half_dots;
            break;
        }
    }
    gbb_accept_stepper_init(stepper, instance, on_pcm, st);

    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = stepper;
    config.script = &smoke->script;
    config.predicate = smoke->predicate;
    config.expect_hw = 0u;
    config.budget_half_dots = PLAYER_SCRIPT_SMOKE_BUDGET_HALF_DOTS;
    config.tail_half_dots = PLAYER_SCRIPT_SMOKE_TAIL_HALF_DOTS;
    config.max_batch = PLAYER_SCRIPT_SMOKE_MAX_BATCH;
    config.deliver = on_deliver;
    config.after_step = on_after_step;
    config.context = st;
    gbb_accept_drive_result driven;
    gbb_accept_drive(&config, &driven);

    result->status = driven.status;
    result->t_hit_half_dots = driven.t_hit_half_dots;
    gbb_accept_pcm_digest_final(&st->digest, result->pcm_sha256);
    result->pcm_nonsilent = st->window.samples != 0u && gbb_accept_pcm_audible(&st->window);
    free(stepper);
    free(st);
    return true;
}
