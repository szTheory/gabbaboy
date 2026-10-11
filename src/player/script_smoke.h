#ifndef GABBABOY_PLAYER_SCRIPT_SMOKE_H
#define GABBABOY_PLAYER_SCRIPT_SMOKE_H

/* Scripted player smoke (D-36). The player replays a gbinput 1 script through
 * the same stepper, driver and predicate the headless runner uses, so the only
 * difference between the two runs is where input events enter the guest (the
 * player's keyboard path) and where PCM goes afterwards (the session audio
 * buffer). This module owns everything that does not need SDL events. */

#include "audio.h"
#include "gbb_accept.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PLAYER_SCRIPT_SMOKE_ROM_LIMIT (8u * 1024u * 1024u)
#define PLAYER_SCRIPT_SMOKE_BUDGET_HALF_DOTS UINT64_C(505612800)
#define PLAYER_SCRIPT_SMOKE_TAIL_HALF_DOTS UINT64_C(8388608)
/* The player's normal input capacity (PLAYER_INPUT_NORMAL_CAPACITY). */
#define PLAYER_SCRIPT_SMOKE_MAX_BATCH 56u
#define PLAYER_SCRIPT_SMOKE_PREDICATE "libbet-tutorial-cleared"

typedef struct {
    gbb_accept_script script;
    const gbb_accept_predicate *predicate;
    uint8_t *rom;
    size_t rom_length;
    char rom_sha256[65];
} player_script_smoke;

/* Reads and validates the script and ROM without touching any guest or player
 * state. Returns 0 on success; nonzero with a message in err otherwise. */
int player_script_smoke_prepare(player_script_smoke *smoke, const char *rom_path,
                                const char *script_path, char *err, size_t err_capacity);
void player_script_smoke_release(player_script_smoke *smoke);

typedef struct {
    gbb_accept_drive_status status;
    uint64_t t_hit_half_dots;
    bool pcm_nonsilent;
    char pcm_sha256[65];
} player_script_smoke_result;

/* Called with each batch of script events (absolute half-dot times). */
typedef bool (*player_script_smoke_deliver_fn)(void *context, const gbb_input_event *events,
                                               size_t count);
/* Called after each stepping window with the instance's actual elapsed time. */
typedef void (*player_script_smoke_progress_fn)(void *context, uint64_t actual_half_dots);

/* Drives an instance that already holds the prepared ROM at emulated time
 * zero. The PCM digest and statistics are taken here, before the frames are
 * handed to audio (which may be NULL). The allocation of the stepper's PCM
 * buffer happens on the heap. Returns false only for an allocation failure. */
bool player_script_smoke_run(const player_script_smoke *smoke, gbb_instance *instance,
                             player_audio *audio, player_script_smoke_deliver_fn deliver,
                             player_script_smoke_progress_fn progress, void *context,
                             player_script_smoke_result *result);

#endif
