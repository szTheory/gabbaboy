#include "audio.h"

#include <SDL3/SDL.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

#define PLAYER_AUDIO_RING_FRAMES 4096u
#define PLAYER_AUDIO_RING_MASK (PLAYER_AUDIO_RING_FRAMES - 1u)
#define PLAYER_AUDIO_TARGET_FRAMES 1606u
#define PLAYER_AUDIO_RING_LIMIT_FRAMES 3214u
#define PLAYER_AUDIO_CALLBACK_CHUNK 256u
#define PLAYER_AUDIO_GAIN_STEP 0.1f

_Static_assert((PLAYER_AUDIO_RING_FRAMES & PLAYER_AUDIO_RING_MASK) == 0u,
               "the SPSC ring capacity must be a power of two");
_Static_assert(sizeof(gbb_audio_frame) == 4u,
               "the player expects packed interleaved s16 stereo frames");

struct player_audio {
    SDL_AudioStream *stream;
    bool sink_available;
    atomic_uint read_index;
    atomic_uint write_index;
    atomic_uint high_water_frames;
    atomic_uint_fast64_t underflow_frames;
    atomic_uint_fast64_t underflow_events;
    atomic_uint_fast64_t backpressure_events;
    atomic_uint_fast64_t unavailable_frames;
    atomic_uint_fast64_t sink_failures;
    atomic_uint_fast64_t flushed_bytes;
    float gain;
    uint8_t pending_frame[sizeof(gbb_audio_frame)];
    unsigned pending_offset;
    unsigned underflow_partial_bytes;
    gbb_audio_frame ring[PLAYER_AUDIO_RING_FRAMES];
};

static void counter_add(atomic_uint_fast64_t *counter, uint_fast64_t amount) {
    uint_fast64_t value = atomic_load_explicit(counter, memory_order_relaxed);
    for (;;) {
        const uint_fast64_t next = UINT_FAST64_MAX - value < amount
            ? UINT_FAST64_MAX : value + amount;
        if (atomic_compare_exchange_weak_explicit(counter, &value, next,
                memory_order_relaxed, memory_order_relaxed)) return;
    }
}

static unsigned player_audio_used(const player_audio *audio) {
    const unsigned write = atomic_load_explicit(&audio->write_index,
                                                 memory_order_relaxed);
    const unsigned read = atomic_load_explicit(&audio->read_index,
                                                memory_order_acquire);
    return write - read;
}

static bool player_audio_stream_write(void *userdata,
                                      const void *bytes,
                                      size_t byte_count) {
    SDL_AudioStream *stream = userdata;
    return SDL_PutAudioStreamData(stream, bytes, (int)byte_count);
}

static void player_audio_transfer(player_audio *audio, int requested_bytes,
                                  player_audio_write_fn write_fn,
                                  void *userdata) {
    if (requested_bytes <= 0 || write_fn == NULL) return;

    /* SDL gives bytes as a positive int; ceil avoids signed addition overflow. */
    unsigned remaining = (unsigned)requested_bytes;
    uint8_t block[PLAYER_AUDIO_CALLBACK_CHUNK * sizeof(gbb_audio_frame)];
    bool underflow_event = false;
    while (remaining != 0u) {
        const unsigned count = remaining < sizeof(block)
            ? remaining : (unsigned)sizeof(block);
        unsigned offset = 0u;
        unsigned missing_bytes = 0u;
        while (offset < count) {
            if (audio->pending_offset == 0u) {
                const unsigned read = atomic_load_explicit(&audio->read_index,
                                                            memory_order_relaxed);
                const unsigned write = atomic_load_explicit(&audio->write_index,
                                                             memory_order_acquire);
                if (read == write) {
                    missing_bytes = count - offset;
                    memset(block + offset, 0, missing_bytes);
                    offset = count;
                    break;
                }
                const gbb_audio_frame frame =
                    audio->ring[read & PLAYER_AUDIO_RING_MASK];
                memcpy(audio->pending_frame, &frame, sizeof(frame));
                atomic_store_explicit(&audio->read_index, read + 1u,
                                      memory_order_release);
            }
            const unsigned frame_remaining =
                (unsigned)sizeof(gbb_audio_frame) - audio->pending_offset;
            const unsigned copy = count - offset < frame_remaining
                ? count - offset : frame_remaining;
            memcpy(block + offset, audio->pending_frame + audio->pending_offset,
                   copy);
            offset += copy;
            audio->pending_offset += copy;
            if (audio->pending_offset == sizeof(gbb_audio_frame))
                audio->pending_offset = 0u;
        }
        if (missing_bytes != 0u) {
            underflow_event = true;
            const unsigned absent = audio->underflow_partial_bytes + missing_bytes;
            counter_add(&audio->underflow_frames,
                        absent / (unsigned)sizeof(gbb_audio_frame));
            audio->underflow_partial_bytes =
                absent % (unsigned)sizeof(gbb_audio_frame);
        }
        if (!write_fn(userdata, block, count)) {
            if (underflow_event)
                counter_add(&audio->underflow_events, 1u);
            counter_add(&audio->sink_failures, 1u);
            return;
        }
        remaining -= count;
    }
    if (underflow_event) counter_add(&audio->underflow_events, 1u);
}

static void SDLCALL player_audio_get(void *userdata, SDL_AudioStream *stream,
                                     int additional_amount, int total_amount) {
    (void)total_amount;
    player_audio *audio = userdata;
    player_audio_transfer(audio, additional_amount, player_audio_stream_write,
                          stream);
}

static bool player_audio_counters_lock_free(player_audio *audio) {
    return atomic_is_lock_free(&audio->read_index) &&
        atomic_is_lock_free(&audio->write_index) &&
        atomic_is_lock_free(&audio->high_water_frames) &&
        atomic_is_lock_free(&audio->underflow_frames) &&
        atomic_is_lock_free(&audio->underflow_events) &&
        atomic_is_lock_free(&audio->backpressure_events) &&
        atomic_is_lock_free(&audio->unavailable_frames) &&
        atomic_is_lock_free(&audio->sink_failures);
}

static void player_audio_init(player_audio *audio) {
    atomic_init(&audio->read_index, 0u);
    atomic_init(&audio->write_index, 0u);
    atomic_init(&audio->high_water_frames, 0u);
    atomic_init(&audio->underflow_frames, 0u);
    atomic_init(&audio->underflow_events, 0u);
    atomic_init(&audio->backpressure_events, 0u);
    atomic_init(&audio->unavailable_frames, 0u);
    atomic_init(&audio->sink_failures, 0u);
    atomic_init(&audio->flushed_bytes, 0u);
    audio->gain = 1.0f;
}

static bool player_audio_close(player_audio *audio);

static bool player_audio_open(player_audio *audio) {
    if (!player_audio_counters_lock_free(audio)) return false;
    const SDL_AudioSpec spec = {SDL_AUDIO_S16, 2, 48000};
    audio->stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,
                                               &spec, player_audio_get, audio);
    if (audio->stream == NULL) return false;
    if (!SDL_SetAudioStreamGain(audio->stream, audio->gain) ||
        !SDL_ResumeAudioStreamDevice(audio->stream)) {
        (void)player_audio_close(audio);
        return false;
    }
    audio->sink_available = true;
    return true;
}

unsigned player_audio_capacity(const player_audio *audio) {
    if (audio == NULL) return 0u;
    const unsigned used = player_audio_used(audio);
    return used >= PLAYER_AUDIO_RING_LIMIT_FRAMES
        ? 0u : PLAYER_AUDIO_RING_LIMIT_FRAMES - used;
}

unsigned player_audio_target_frames(void) {
    return PLAYER_AUDIO_TARGET_FRAMES;
}

unsigned player_audio_ring_ceiling_frames(void) {
    return PLAYER_AUDIO_RING_LIMIT_FRAMES;
}

bool player_audio_submit(player_audio *audio, const gbb_audio_frame *frames,
                         unsigned count) {
    if (audio == NULL || (count != 0u && frames == NULL)) return false;
    if (!audio->sink_available) {
        counter_add(&audio->unavailable_frames, count);
        return true;
    }

    const unsigned write = atomic_load_explicit(&audio->write_index,
                                                memory_order_relaxed);
    const unsigned read = atomic_load_explicit(&audio->read_index,
                                               memory_order_acquire);
    const unsigned used = write - read;
    if (used > PLAYER_AUDIO_RING_LIMIT_FRAMES ||
        count > PLAYER_AUDIO_RING_LIMIT_FRAMES - used) {
        counter_add(&audio->backpressure_events, 1u);
        return false;
    }
    for (unsigned i = 0u; i < count; ++i)
        audio->ring[(write + i) & PLAYER_AUDIO_RING_MASK] = frames[i];
    atomic_store_explicit(&audio->write_index, write + count,
                          memory_order_release);

    const unsigned high = used + count;
    unsigned previous = atomic_load_explicit(&audio->high_water_frames,
                                              memory_order_relaxed);
    while (high > previous && !atomic_compare_exchange_weak_explicit(
            &audio->high_water_frames, &previous, high,
            memory_order_relaxed, memory_order_relaxed)) { }
    return true;
}

bool player_audio_clear(player_audio *audio) {
    if (audio == NULL) return false;
    SDL_AudioStream *stream = audio->stream;
    bool paused_by_us = false;
    if (stream != NULL) {
        if (!SDL_AudioStreamDevicePaused(stream))
            paused_by_us = SDL_PauseAudioStreamDevice(stream);
        if (!SDL_LockAudioStream(stream)) {
            if (paused_by_us) (void)SDL_ResumeAudioStreamDevice(stream);
            return false;
        }
    }

    const unsigned write = atomic_load_explicit(&audio->write_index,
                                                memory_order_relaxed);
    const unsigned read = atomic_load_explicit(&audio->read_index,
                                               memory_order_acquire);
    const unsigned queued_frames = write - read;
    uint_fast64_t discard_bytes =
        (uint_fast64_t)queued_frames * sizeof(gbb_audio_frame);
    if (audio->pending_offset != 0u)
        discard_bytes += sizeof(gbb_audio_frame) - audio->pending_offset;
    if (stream != NULL) {
        const int queued = SDL_GetAudioStreamQueued(stream);
        if (queued > 0 && UINT_FAST64_MAX - discard_bytes >= (uint_fast64_t)queued)
            discard_bytes += (uint_fast64_t)queued;
        else if (queued > 0)
            discard_bytes = UINT_FAST64_MAX;
        if (!SDL_ClearAudioStream(stream)) {
            (void)SDL_UnlockAudioStream(stream);
            if (paused_by_us) (void)SDL_ResumeAudioStreamDevice(stream);
            return false;
        }
    }

    atomic_store_explicit(&audio->read_index, write, memory_order_release);
    audio->pending_offset = 0u;
    audio->underflow_partial_bytes = 0u;
    counter_add(&audio->flushed_bytes, discard_bytes);

    if (stream != NULL) {
        const bool unlocked = SDL_UnlockAudioStream(stream);
        const bool resumed = !paused_by_us || SDL_ResumeAudioStreamDevice(stream);
        if (!unlocked || !resumed) return false;
    }
    return true;
}

uint_fast64_t player_audio_flushed_bytes(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->flushed_bytes,
                                                     memory_order_relaxed);
}

bool player_audio_handle_device_event(player_audio *audio, uint32_t event_type,
                                      uint32_t device_id, bool recording) {
    (void)device_id;
    if (audio == NULL) return false;
    if (recording) return true;
    if (event_type == SDL_EVENT_AUDIO_DEVICE_REMOVED) {
        if (!player_audio_clear(audio)) return false;
        if (audio->stream == NULL) {
            audio->sink_available = false;
            return true;
        }
        const SDL_AudioDeviceID bound = SDL_GetAudioStreamDevice(audio->stream);
        if (bound != 0 && !SDL_AudioStreamDevicePaused(audio->stream)) {
            /* SDL's default-device stream migrated successfully. */
            audio->sink_available = true;
            return true;
        }
        if (!player_audio_close(audio)) {
            audio->sink_available = false;
            return false;
        }
        audio->sink_available = false;
        return true;
    }
    if (event_type == SDL_EVENT_AUDIO_DEVICE_ADDED) {
        if (audio->stream != NULL && audio->sink_available)
            return player_audio_clear(audio);
        if (audio->stream != NULL && !player_audio_close(audio)) return false;
        audio->sink_available = false;
        if (!player_audio_open(audio)) return false;
        return player_audio_clear(audio);
    }
    return false;
}

static bool player_audio_close(player_audio *audio) {
    if (audio == NULL || audio->stream == NULL) return true;
    SDL_AudioStream *stream = audio->stream;
    (void)SDL_PauseAudioStreamDevice(stream);
    if (SDL_LockAudioStream(stream)) {
        (void)SDL_SetAudioStreamGetCallback(stream, NULL, NULL);
        (void)SDL_UnlockAudioStream(stream);
    } else {
        /* Keep the callback userdata alive if SDL cannot establish quiescence. */
        return false;
    }
    SDL_DestroyAudioStream(stream);
    audio->stream = NULL;
    audio->sink_available = false;
    return true;
}

player_audio *player_audio_create(void) {
    player_audio *audio = calloc(1u, sizeof(*audio));
    if (audio == NULL) return NULL;
    player_audio_init(audio);
    /* A missing sink is a supported state; submissions are counted and dropped. */
    (void)player_audio_open(audio);
    return audio;
}

void player_audio_destroy(player_audio *audio) {
    if (audio == NULL) return;
    if (!player_audio_close(audio)) return;
    free(audio);
}

void player_audio_note_backpressure(player_audio *audio) {
    if (audio != NULL) counter_add(&audio->backpressure_events, 1u);
}

uint_fast64_t player_audio_underflow(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->underflow_frames,
                                                     memory_order_relaxed);
}

uint_fast64_t player_audio_underflow_events(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->underflow_events,
                                                     memory_order_relaxed);
}

uint_fast64_t player_audio_backpressure_events(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(
        &audio->backpressure_events, memory_order_relaxed);
}

unsigned player_audio_high_water(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->high_water_frames,
                                                      memory_order_relaxed);
}

float player_audio_gain(const player_audio *audio) {
    return audio == NULL ? 1.0f : audio->gain;
}

bool player_audio_adjust_gain(player_audio *audio, int direction) {
    if (audio == NULL || (direction != -1 && direction != 1)) return false;
    float next = audio->gain + (float)direction * PLAYER_AUDIO_GAIN_STEP;
    if (next < 0.0f) next = 0.0f;
    if (next > 2.0f) next = 2.0f;
    if (audio->stream != NULL && !SDL_SetAudioStreamGain(audio->stream, next))
        return false;
    audio->gain = next;
    return true;
}

uint_fast64_t player_audio_sink_failures(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->sink_failures,
                                                     memory_order_relaxed);
}

bool player_audio_available(const player_audio *audio) {
    return audio != NULL && audio->sink_available;
}

uint_fast64_t player_audio_unavailable_frames(const player_audio *audio) {
    return audio == NULL ? 0u : atomic_load_explicit(&audio->unavailable_frames,
                                                      memory_order_relaxed);
}

uint64_t player_audio_queued_input_bytes(const player_audio *audio) {
    if (audio == NULL || audio->stream == NULL) return 0u;
    const int queued = SDL_GetAudioStreamQueued(audio->stream);
    return queued > 0 ? (uint64_t)queued : 0u;
}

#ifdef GBB_PLAYER_AUDIO_TESTING
player_audio *player_audio_test_create(bool available) {
    player_audio *audio = calloc(1u, sizeof(*audio));
    if (audio != NULL) {
        player_audio_init(audio);
        audio->sink_available = available;
    }
    return audio;
}

void player_audio_test_callback(player_audio *audio, int requested_bytes,
                                player_audio_write_fn write_fn,
                                void *userdata) {
    if (audio != NULL)
        player_audio_transfer(audio, requested_bytes, write_fn, userdata);
}

bool player_audio_test_set_indices(player_audio *audio, unsigned read,
                                   unsigned write) {
    if (audio == NULL || read != write) return false;
    atomic_store_explicit(&audio->read_index, read, memory_order_relaxed);
    atomic_store_explicit(&audio->write_index, write, memory_order_relaxed);
    return true;
}

unsigned player_audio_test_queued(const player_audio *audio) {
    return audio == NULL ? 0u : player_audio_used(audio);
}

bool player_audio_test_drop_device(player_audio *audio) {
    if (audio == NULL || audio->stream == NULL) return false;
    return player_audio_close(audio);
}
#endif
