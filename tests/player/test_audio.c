#include "audio.h"
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
    return 1; \
} } while (0)

typedef struct {
    uint8_t bytes[400000];
    size_t count;
} capture;

static bool capture_frames(void *userdata, const void *bytes,
                           size_t byte_count) {
    capture *output = userdata;
    if (byte_count > sizeof(output->bytes) - output->count) return false;
    memcpy(output->bytes + output->count, bytes, byte_count);
    output->count += byte_count;
    return true;
}

static bool reject_frames(void *userdata, const void *bytes,
                          size_t byte_count) {
    (void)bytes;
    (void)byte_count;
    unsigned *calls = userdata;
    ++*calls;
    return false;
}

static gbb_audio_frame frame_for(unsigned sequence) {
    gbb_audio_frame frame = {
        (int16_t)(sequence & 0x7fffu),
        (int16_t)(-(int32_t)(sequence & 0x7fffu))
    };
    return frame;
}

static int player_audio_ring(void) {
    player_audio *audio = player_audio_test_create(true);
    REQUIRE(audio != NULL);
    REQUIRE(player_audio_capacity(audio) >= 1600u);
    gbb_audio_frame input[16];
    for (unsigned i = 0; i < 16u; ++i) input[i] = frame_for(i + 1u);
    REQUIRE(player_audio_submit(audio, input, 12u));
    REQUIRE(player_audio_capacity(audio) + 12u >= 1600u);
    capture output = {0};
    player_audio_test_callback(audio, 0, capture_frames, &output);
    REQUIRE(output.count == 0u);
    player_audio_test_callback(audio, 1, capture_frames, &output);
    REQUIRE(output.count == 1u && memcmp(output.bytes, input, 1u) == 0);
    player_audio_test_callback(audio, 7, capture_frames, &output);
    REQUIRE(output.count == 8u);
    REQUIRE(memcmp(output.bytes, input, 8u) == 0);
    REQUIRE(player_audio_underflow(audio) == 0u);

    player_audio_test_callback(audio, 13, capture_frames, &output);
    REQUIRE(output.count == 21u);
    REQUIRE(memcmp(output.bytes + 8u, (const uint8_t *)input + 8u, 13u) == 0);
    player_audio_test_callback(audio, 9, capture_frames, &output);
    REQUIRE(output.count == 30u);
    player_audio_test_callback(audio, 13, capture_frames, &output);
    REQUIRE(output.count == 43u);
    REQUIRE(memcmp(output.bytes, input, output.count) == 0);
    player_audio_test_callback(audio, 25, capture_frames, &output);
    REQUIRE(output.count == 68u);
    REQUIRE(memcmp(output.bytes + 43u, (const uint8_t *)input + 43u, 5u) == 0);
    for (size_t i = 48u; i < 68u; ++i) REQUIRE(output.bytes[i] == 0u);
    REQUIRE(player_audio_underflow(audio) == 5u);

    const int boundary_bytes = 2147483644;
    REQUIRE(player_audio_submit(audio, input, 12u));
    unsigned calls = 0u;
    player_audio_test_callback(audio, boundary_bytes, reject_frames, &calls);
    REQUIRE(calls == 1u);
    REQUIRE(player_audio_sink_failures(audio) == 1u);
    REQUIRE(player_audio_high_water(audio) >= 12u);
    REQUIRE(player_audio_backpressure_events(audio) == 0u);
    player_audio_destroy(audio);
    return 0;
}

typedef struct {
    player_audio *audio;
    capture output;
} concurrent_context;

static int produce_sequence(void *userdata) {
    concurrent_context *context = userdata;
    gbb_audio_frame frames[32];
    unsigned sequence = 0u;
    while (sequence < 100000u) {
        unsigned count = 100000u - sequence;
        if (count > 32u) count = 32u;
        for (unsigned i = 0u; i < count; ++i)
            frames[i] = frame_for(sequence + i + 1u);
        if (player_audio_submit(context->audio, frames, count))
            sequence += count;
        else
            SDL_Delay(0);
    }
    return 0;
}

static int consume_sequence(void *userdata) {
    concurrent_context *context = userdata;
    while (context->output.count < 100000u * sizeof(gbb_audio_frame)) {
        if (player_audio_test_queued(context->audio) >= 32u)
            player_audio_test_callback(context->audio, 128, capture_frames,
                                       &context->output);
        else
            SDL_Delay(0);
    }
    return 0;
}

static int player_audio_concurrent(void) {
    player_audio *audio = player_audio_test_create(true);
    REQUIRE(audio != NULL);
    concurrent_context context = {0};
    context.audio = audio;
    SDL_Thread *producer = SDL_CreateThread(produce_sequence, "audio producer",
                                            &context);
    SDL_Thread *consumer = SDL_CreateThread(consume_sequence, "audio consumer",
                                            &context);
    REQUIRE(producer != NULL && consumer != NULL);
    SDL_WaitThread(producer, NULL);
    SDL_WaitThread(consumer, NULL);
    capture *output = &context.output;
    REQUIRE(output->count == 100000u * sizeof(gbb_audio_frame));
    for (unsigned i = 0u; i < 100000u; ++i) {
        const gbb_audio_frame expected = frame_for(i + 1u);
        REQUIRE(memcmp(output->bytes + i * sizeof(expected), &expected,
                       sizeof(expected)) == 0);
    }
    REQUIRE(player_audio_test_set_indices(audio, UINT32_MAX - 7u,
                                          UINT32_MAX - 7u));
    gbb_audio_frame wrap_frames[16];
    for (unsigned i = 0u; i < 16u; ++i)
        wrap_frames[i] = frame_for(i + 50u);
    REQUIRE(player_audio_submit(audio, wrap_frames, 16u));
    capture wrapped = {0};
    player_audio_test_callback(audio, 64, capture_frames, &wrapped);
    REQUIRE(wrapped.count == 16u * sizeof(*wrap_frames) &&
            memcmp(wrapped.bytes, wrap_frames,
                   16u * sizeof(*wrap_frames)) == 0);
    player_audio_destroy(audio);
    return 0;
}

static int player_audio_pacing(void) {
    player_audio *audio = player_audio_test_create(true);
    REQUIRE(audio != NULL);
    const unsigned initial = player_audio_capacity(audio);
    gbb_audio_frame *frames = calloc(initial, sizeof(*frames));
    REQUIRE(frames != NULL);
    REQUIRE(player_audio_submit(audio, frames, initial));
    REQUIRE(player_audio_capacity(audio) == 0u);
    REQUIRE(!player_audio_submit(audio, frames, 1u));
    REQUIRE(player_audio_backpressure_events(audio) == 1u);
    REQUIRE(player_audio_high_water(audio) == initial);
    capture output = {0};
    player_audio_test_callback(audio, (int)(initial * 4u), capture_frames,
                               &output);
    REQUIRE(output.count == (size_t)initial * sizeof(*frames) &&
            player_audio_capacity(audio) == initial);
    free(frames);
    player_audio_destroy(audio);
    return 0;
}

static int test_player_audio_gain(void) {
    player_audio *audio = player_audio_test_create(true);
    REQUIRE(audio != NULL);
    REQUIRE(player_audio_gain(audio) == 1.0f);
    REQUIRE(player_audio_adjust_gain(audio, 1));
    REQUIRE(player_audio_gain(audio) > 1.0f);
    REQUIRE(player_audio_adjust_gain(audio, -1));
    REQUIRE(player_audio_gain(audio) == 1.0f);
    for (unsigned i = 0u; i < 32u; ++i)
        REQUIRE(player_audio_adjust_gain(audio, 1));
    REQUIRE(player_audio_gain(audio) <= 2.0f);
    REQUIRE(!player_audio_adjust_gain(audio, 0));
    player_audio_destroy(audio);
    return 0;
}

static int player_audio_unavailable(void) {
    player_audio *audio = player_audio_test_create(false);
    REQUIRE(audio != NULL);
    REQUIRE(!player_audio_available(audio));
    gbb_audio_frame frames[13] = {{0}};
    REQUIRE(player_audio_submit(audio, frames, 13u));
    REQUIRE(player_audio_unavailable_frames(audio) == 13u);
    REQUIRE(player_audio_capacity(audio) >= 1600u);
    REQUIRE(player_audio_underflow(audio) == 0u);
    REQUIRE(player_audio_sink_failures(audio) == 0u);
    player_audio_destroy(audio);

    REQUIRE(SDL_SetHint(SDL_HINT_AUDIO_DRIVER, "dummy"));
    REQUIRE(SDL_Init(SDL_INIT_AUDIO));
    player_audio *dummy = player_audio_create();
    REQUIRE(dummy != NULL && player_audio_available(dummy));
    gbb_audio_frame signal[8];
    for (unsigned i = 0u; i < 8u; ++i) signal[i] = frame_for(i + 1u);
    REQUIRE(player_audio_submit(dummy, signal, 8u));
    REQUIRE(player_audio_queued_input_bytes(dummy) <= 4096u);
    player_audio_destroy(dummy);
    SDL_QuitSubSystem(SDL_INIT_AUDIO);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "player_audio_ring") == 0) return player_audio_ring();
    if (strcmp(argv[1], "player_audio_concurrent") == 0)
        return player_audio_concurrent();
    if (strcmp(argv[1], "player_audio_pacing") == 0)
        return player_audio_pacing();
    if (strcmp(argv[1], "player_audio_gain") == 0)
        return test_player_audio_gain();
    if (strcmp(argv[1], "player_audio_unavailable") == 0)
        return player_audio_unavailable();
    return 2;
}
