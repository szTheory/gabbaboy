#include <SDL3/SDL.h>
#include "gabbaboy/gabbaboy.h"
#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define PLAYER_AUDIO_RING_FRAMES 4096u
#define PLAYER_AUDIO_RING_LIMIT_FRAMES 3214u
#define PLAYER_AUDIO_CALLBACK_CHUNK 256u

typedef struct player_audio player_audio;
struct player_audio {
    SDL_AudioStream *stream;
    atomic_uint read_index;
    atomic_uint write_index;
    atomic_uint underflow_frames;
    atomic_uint backpressure_frames;
    atomic_uint high_water_frames;
    gbb_audio_frame ring[PLAYER_AUDIO_RING_FRAMES];
};

static unsigned player_audio_used(const player_audio *audio) {
    const unsigned write = atomic_load_explicit(&audio->write_index, memory_order_acquire);
    const unsigned read = atomic_load_explicit(&audio->read_index, memory_order_acquire);
    return write - read;
}

static void SDLCALL player_audio_get(void *userdata, SDL_AudioStream *stream,
                                     int additional_amount, int total_amount) {
    (void)total_amount;
    player_audio *audio = userdata;
    if (additional_amount <= 0) return;
    unsigned remaining = ((unsigned)additional_amount + sizeof(gbb_audio_frame) - 1u) /
                         sizeof(gbb_audio_frame);
    gbb_audio_frame block[PLAYER_AUDIO_CALLBACK_CHUNK];
    unsigned missing = 0u;
    while (remaining != 0u) {
        const unsigned count = remaining < PLAYER_AUDIO_CALLBACK_CHUNK
            ? remaining : PLAYER_AUDIO_CALLBACK_CHUNK;
        unsigned read = atomic_load_explicit(&audio->read_index, memory_order_relaxed);
        const unsigned write = atomic_load_explicit(&audio->write_index, memory_order_acquire);
        unsigned available = write - read;
        const unsigned copied = available < count ? available : count;
        for (unsigned i = 0u; i < copied; ++i)
            block[i] = audio->ring[(read + i) & (PLAYER_AUDIO_RING_FRAMES - 1u)];
        if (copied != 0u)
            atomic_store_explicit(&audio->read_index, read + copied, memory_order_release);
        if (copied < count) {
            memset(block + copied, 0, (count - copied) * sizeof(*block));
            missing += count - copied;
        }
        if (!SDL_PutAudioStreamData(stream, block, (int)(count * sizeof(*block))))
            atomic_fetch_add_explicit(&audio->underflow_frames, count, memory_order_relaxed);
        remaining -= count;
    }
    if (missing != 0u)
        atomic_fetch_add_explicit(&audio->underflow_frames, missing, memory_order_relaxed);
}

static bool player_audio_open(player_audio *audio) {
    atomic_init(&audio->read_index, 0u);
    atomic_init(&audio->write_index, 0u);
    atomic_init(&audio->underflow_frames, 0u);
    atomic_init(&audio->backpressure_frames, 0u);
    atomic_init(&audio->high_water_frames, 0u);
    if (!atomic_is_lock_free(&audio->read_index) ||
        !atomic_is_lock_free(&audio->write_index) ||
        !atomic_is_lock_free(&audio->underflow_frames) ||
        !atomic_is_lock_free(&audio->backpressure_frames) ||
        !atomic_is_lock_free(&audio->high_water_frames)) return false;
    const SDL_AudioSpec spec = {SDL_AUDIO_S16, 2, 48000};
    audio->stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,
                                               &spec, player_audio_get, audio);
    if (audio->stream == NULL) return false;
    return SDL_ResumeAudioStreamDevice(audio->stream);
}

unsigned player_audio_capacity(const player_audio *audio) {
    const unsigned used = player_audio_used(audio);
    return used >= PLAYER_AUDIO_RING_LIMIT_FRAMES ? 0u : PLAYER_AUDIO_RING_LIMIT_FRAMES - used;
}

bool player_audio_submit(player_audio *audio, const gbb_audio_frame *frames,
                         unsigned count) {
    const unsigned write = atomic_load_explicit(&audio->write_index, memory_order_relaxed);
    const unsigned read = atomic_load_explicit(&audio->read_index, memory_order_acquire);
    const unsigned used = write - read;
    if (count > PLAYER_AUDIO_RING_LIMIT_FRAMES - used) {
        atomic_fetch_add_explicit(&audio->backpressure_frames, count, memory_order_relaxed);
        return false;
    }
    for (unsigned i = 0u; i < count; ++i)
        audio->ring[(write + i) & (PLAYER_AUDIO_RING_FRAMES - 1u)] = frames[i];
    atomic_store_explicit(&audio->write_index, write + count, memory_order_release);
    const unsigned high = used + count;
    unsigned previous = atomic_load_explicit(&audio->high_water_frames, memory_order_relaxed);
    while (high > previous && !atomic_compare_exchange_weak_explicit(
            &audio->high_water_frames, &previous, high,
            memory_order_relaxed, memory_order_relaxed)) { }
    return true;
}

void player_audio_close(player_audio *audio) {
    if (audio->stream != NULL) {
        SDL_PauseAudioStreamDevice(audio->stream);
        SDL_SetAudioStreamGetCallback(audio->stream, NULL, NULL);
        SDL_DestroyAudioStream(audio->stream);
        audio->stream = NULL;
    }
}

player_audio *player_audio_create(void) {
    player_audio *audio = calloc(1u, sizeof(*audio));
    if (audio == NULL) return NULL;
    if (!player_audio_open(audio)) {
        player_audio_close(audio);
        free(audio);
        return NULL;
    }
    return audio;
}

void player_audio_destroy(player_audio *audio) {
    if (audio == NULL) return;
    player_audio_close(audio);
    free(audio);
}

unsigned player_audio_underflow(const player_audio *audio) {
    return atomic_load_explicit(&audio->underflow_frames, memory_order_relaxed);
}

unsigned player_audio_backpressure(const player_audio *audio) {
    return atomic_load_explicit(&audio->backpressure_frames, memory_order_relaxed);
}

unsigned player_audio_high_water(const player_audio *audio) {
    return atomic_load_explicit(&audio->high_water_frames, memory_order_relaxed);
}
