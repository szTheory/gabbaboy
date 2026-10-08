#ifndef GABBABOY_PLAYER_AUDIO_H
#define GABBABOY_PLAYER_AUDIO_H

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct player_audio player_audio;
typedef bool (*player_audio_write_fn)(void *userdata, const void *bytes,
                                      size_t byte_count);

player_audio *player_audio_create(void);
void player_audio_destroy(player_audio *audio);
unsigned player_audio_capacity(const player_audio *audio);
unsigned player_audio_target_frames(void);
unsigned player_audio_ring_ceiling_frames(void);
bool player_audio_submit(player_audio *audio, const gbb_audio_frame *frames,
                         unsigned count);
bool player_audio_clear(player_audio *audio);
uint_fast64_t player_audio_flushed_bytes(const player_audio *audio);
bool player_audio_handle_device_event(player_audio *audio, uint32_t event_type,
                                      uint32_t device_id, bool recording);
uint_fast64_t player_audio_underflow(const player_audio *audio);
uint_fast64_t player_audio_underflow_events(const player_audio *audio);
uint_fast64_t player_audio_backpressure_events(const player_audio *audio);
void player_audio_note_backpressure(player_audio *audio);
unsigned player_audio_high_water(const player_audio *audio);
float player_audio_gain(const player_audio *audio);
bool player_audio_adjust_gain(player_audio *audio, int direction);
uint_fast64_t player_audio_sink_failures(const player_audio *audio);
uint_fast64_t player_audio_sink_failure_pcm_bytes(const player_audio *audio);
bool player_audio_available(const player_audio *audio);
uint_fast64_t player_audio_unavailable_frames(const player_audio *audio);
uint64_t player_audio_queued_input_bytes(const player_audio *audio);

#ifdef GBB_PLAYER_AUDIO_TESTING
player_audio *player_audio_test_create(bool available);
void player_audio_test_callback(player_audio *audio, int requested_bytes,
                               player_audio_write_fn write_fn, void *userdata);
bool player_audio_test_set_indices(player_audio *audio, unsigned read,
                                   unsigned write);
unsigned player_audio_test_queued(const player_audio *audio);
bool player_audio_test_drop_device(player_audio *audio);
#endif

#endif
