#ifndef GABBABOY_PLAYER_SLOTS_H
#define GABBABOY_PLAYER_SLOTS_H

/* SDL-free slot engine for the player's numbered save-state slots (Phase 18, D-21..D-25).
 *
 * It saves and loads gbb_save_state bytes through the public API only. Files live in the
 * player's pref directory, reached through one directory descriptor the caller opened, and
 * are named from the ROM digest, the created profile and the slot digit alone, so nothing
 * user-controlled ever becomes part of a name (D-22).
 *
 * A load is all-or-nothing (D-23): the slot is validated in a scratch instance first, so a
 * refusal touches no file and no live state, and only then are the battery preload file, the
 * live state and the undo file written, in that order.
 *
 * This header includes only the public API header and libc. It never names SDL, the player
 * session or the acceptance library, so it compiles on every platform and the message table,
 * key decoder and re-anchor plan are tested without a window. */

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PLAYER_SLOT_COUNT 9u
/* One host frame in half-dots (70,224 dots). */
#define PLAYER_SLOT_FRAME_HALF_DOTS UINT64_C(140448)
/* The core's input queue holds 64 events; the player queues eight button releases after a load, so a
 * restored queue may hold at most 64 - 8 = 56 events (a recorded discretion choice, D-24). */
#define PLAYER_SLOT_QUEUE_CAPACITY 64u
#define PLAYER_SLOT_RELEASE_EVENTS 8u
/* A restored queue reaching further than one frame per queue slot past now is unsafe (D-24). */
#define PLAYER_SLOT_UNSAFE_HALF_DOTS (PLAYER_SLOT_FRAME_HALF_DOTS * UINT64_C(64))
/* The store keeps its own copy of the ROM for scratch validation; this is the largest ROM the core loads. */
#define PLAYER_SLOT_MAX_ROM_BYTES (8u * 1024u * 1024u)

typedef enum {
    PLAYER_SLOT_SOURCE_SLOT = 0,
    PLAYER_SLOT_SOURCE_UNDO
} player_slot_source;

typedef enum {
    PLAYER_SLOT_SAVED = 0,
    PLAYER_SLOT_SAVE_FAILED,
    PLAYER_SLOT_LOADED,
    PLAYER_SLOT_UNDONE,
    PLAYER_SLOT_EMPTY,
    PLAYER_SLOT_NO_UNDO,
    PLAYER_SLOT_READ_FAILED,
    PLAYER_SLOT_REFUSED,
    PLAYER_SLOT_BACKUP_FAILED,
    PLAYER_SLOT_UNSAFE_INPUT,
    /* The live machine now holds the loaded state and the load could not finish cleanly: the rollback after a
     * failed undo write was refused, or the input clock could not be read. `error` is the gbb_error. The
     * "nothing changed" outcomes above are only ever returned when that is true. */
    PLAYER_SLOT_RESTORE_FAILED
} player_slot_outcome;

typedef struct {
    player_slot_outcome outcome;
    int error;                /* gbb_error behind the outcome; GBB_OK when a file operation failed */
    unsigned slot;            /* the requested slot (0 for the undo source) */
    player_slot_source source;
    gbb_input_clock clock;    /* the live input clock after LOADED/UNDONE; zero otherwise */
    bool guard_unsaved;       /* LOADED/UNDONE, but the battery guard file could not be written: the next
                               * session may treat this battery as an in-game save and replace the preload */
} player_slot_result;

/* Where the player re-anchors its input after a load (D-24). */
typedef struct {
    uint64_t cursor;          /* the player's input cursor: the restored now */
    uint32_t pending_count;   /* the restored queue length, for the player's pending mirror */
    uint64_t release_at;      /* the time the player queues its releases at: max(now, last queued) */
    bool unsafe;              /* the restored queue is too far ahead or too long to re-anchor */
} player_slot_reanchor;

typedef struct {
    unsigned digit;           /* 1..9 for a digit key, 0 for any other key */
    char letter;              /* 'S', 'L', 'Z' or 'R' (either case) for a letter key, else 0 */
    bool gui;
    bool ctrl;
    bool alt;
    bool repeat;
    bool blocked;             /* a transition, dialog or save-failure prompt is pending */
} player_slot_key_input;

typedef enum {
    PLAYER_SLOT_KEY_NONE = 0,
    PLAYER_SLOT_KEY_SELECT,
    PLAYER_SLOT_KEY_SAVE,
    PLAYER_SLOT_KEY_LOAD,
    PLAYER_SLOT_KEY_UNDO
} player_slot_key_action;

typedef struct {
    int dirfd;                /* borrowed pref-directory descriptor; never closed here */
    gbb_profile profile;
    char prefix[80];          /* `<rom sha256 hex>-<dmg|cgb>` */
    uint8_t *rom;             /* the store's own heap copy of the ROM, for scratch validation */
    size_t rom_size;
    uint8_t *guard;           /* the battery right after the last slot load; persisted as <prefix>-battery-guard.bin */
    size_t guard_size;
    bool guard_valid;
} player_slot_store;

/* Prepares a store and removes this ROM's and profile's stale `.<prefix>-*.tmp-*` writer temps left by a crash.
 * Returns false (with a zeroed store) for a bad descriptor, digest or profile, a ROM larger than
 * PLAYER_SLOT_MAX_ROM_BYTES or an allocation failure; always false on Windows. */
bool player_slot_store_init(player_slot_store *store, int pref_dirfd, const uint8_t rom_sha256[32],
                            gbb_profile profile, const uint8_t *rom, size_t rom_size);
void player_slot_store_free(player_slot_store *store);

/* Writes gbb_save_state(instance) to the slot file (1..9). */
player_slot_result player_slot_save(player_slot_store *store, const gbb_instance *instance, unsigned slot);
/* D-23: loads a slot, or the undo file (a swap), all-or-nothing. */
player_slot_result player_slot_load(player_slot_store *store, gbb_instance *instance,
                                    player_slot_source source, unsigned slot);

/* D-24: the input re-anchor the player applies to a restored clock. Pure. */
player_slot_reanchor player_slot_plan_reanchor(const gbb_input_clock *clock);
/* D-21: pure key decoding. *out_slot receives the digit for PLAYER_SLOT_KEY_SELECT. */
player_slot_key_action player_slot_key_decode(const player_slot_key_input *input, unsigned *out_slot);

/* D-25 status text. All three write a NUL-terminated string that never overruns `out`; capacity 0 or a
 * NULL buffer writes nothing. */
void player_slot_format_message(const player_slot_result *result, char *out, size_t capacity);
void player_slot_format_selection(const player_slot_store *store, unsigned slot, char *out, size_t capacity);
void player_slot_format_log(const player_slot_result *result, char *out, size_t capacity);

#endif
