#include "audio.c"

#include <stdio.h>

#define REQUIRE(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
    return 1; \
} } while (0)

static bool accept_audio(void *userdata, const void *bytes, size_t byte_count) {
    (void)userdata;
    (void)bytes;
    (void)byte_count;
    return true;
}

static bool reject_audio(void *userdata, const void *bytes, size_t byte_count) {
    (void)userdata;
    (void)bytes;
    (void)byte_count;
    return false;
}

int main(void) {
    const uint_fast64_t maximum = UINT_FAST64_MAX;
    const gbb_audio_frame frames[4] = {{0}};

    player_audio *audio = player_audio_test_create(false);
    REQUIRE(audio != NULL);
    atomic_store_explicit(&audio->unavailable_frames, maximum - 2u,
                          memory_order_relaxed);
    REQUIRE(player_audio_submit(audio, frames, 4u));
    REQUIRE(player_audio_unavailable_frames(audio) == maximum);

    atomic_store_explicit(&audio->underflow_frames, maximum - 1u,
                          memory_order_relaxed);
    atomic_store_explicit(&audio->underflow_events, maximum - 1u,
                          memory_order_relaxed);
    player_audio_test_callback(audio, 4, accept_audio, NULL);
    REQUIRE(player_audio_underflow(audio) == maximum);
    REQUIRE(player_audio_underflow_events(audio) == maximum);

    atomic_store_explicit(&audio->sink_failures, maximum - 1u,
                          memory_order_relaxed);
    player_audio_test_callback(audio, 4, reject_audio, NULL);
    REQUIRE(player_audio_sink_failures(audio) == maximum);
    player_audio_destroy(audio);

    audio = player_audio_test_create(true);
    REQUIRE(audio != NULL);
    atomic_store_explicit(&audio->backpressure_events, maximum - 1u,
                          memory_order_relaxed);
    gbb_audio_frame full_ring[3214] = {{0}};
    REQUIRE(player_audio_submit(audio, full_ring, 3214u));
    REQUIRE(!player_audio_submit(audio, frames, 1u));
    REQUIRE(player_audio_backpressure_events(audio) == maximum);

    REQUIRE(player_audio_clear(audio));
    atomic_store_explicit(&audio->flushed_bytes, maximum - 2u,
                          memory_order_relaxed);
    REQUIRE(player_audio_submit(audio, frames, 1u));
    REQUIRE(player_audio_clear(audio));
    REQUIRE(player_audio_flushed_bytes(audio) == maximum);
    player_audio_destroy(audio);

    puts("player_audio_counter_saturation: all public counter paths saturate");
    return 0;
}
