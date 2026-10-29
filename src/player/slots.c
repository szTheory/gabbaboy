/* SDL-free slot engine (Phase 18, D-21..D-25). See slots.h.
 *
 * Everything that touches the file system sits inside #ifndef _WIN32 with ISO C stubs, so this file
 * compiles under MSVC: the native Windows lane builds gabbaboy_player_slots for the pure tables
 * (messages, key decoder, re-anchor plan), which are outside the guard. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "slots.h"

#include "gbb_host.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

void player_slot_store_free(player_slot_store *store) {
    if (store == NULL) return;
    free(store->rom);
    free(store->guard);
    memset(store, 0, sizeof(*store));
    store->dirfd = -1;
}

/* D-24: a restored queue is unsafe to re-anchor when its last event lies more than one frame per queue slot
 * past now, or when it already holds more events than leave room for the eight releases the player queues
 * after a load (more than 56 of the core's 64). A last event before now is time-safe. */
static bool slot_clock_unsafe(const gbb_input_clock *clock) {
    if (clock->last_queued_half_dots > clock->now_half_dots &&
        clock->last_queued_half_dots - clock->now_half_dots > PLAYER_SLOT_UNSAFE_HALF_DOTS)
        return true;
    return clock->queued_count > PLAYER_SLOT_QUEUE_CAPACITY - PLAYER_SLOT_RELEASE_EVENTS;
}

#ifndef _WIN32

typedef enum { NAME_SLOT, NAME_UNDO, NAME_PRELOAD } name_kind;

static const char *profile_token(gbb_profile profile) {
    if (profile == GBB_PROFILE_DMG_CPU_B) return "dmg";
    if (profile == GBB_PROFILE_CGB_CPU_E) return "cgb";
    return NULL;
}

/* D-22: a name is built from the ROM digest, the created profile and a digit only; no caller text. */
static bool build_name(const player_slot_store *store, name_kind kind, unsigned slot, char *out, size_t capacity) {
    int length;
    if (kind == NAME_SLOT) {
        if (slot < 1u || slot > PLAYER_SLOT_COUNT) return false;
        length = snprintf(out, capacity, "%s-slot%u.gbbs", store->prefix, slot);
    } else if (kind == NAME_UNDO) {
        length = snprintf(out, capacity, "%s-undo.gbbs", store->prefix);
    } else {
        length = snprintf(out, capacity, "%s-battery-preload.bin", store->prefix);
    }
    return length > 0 && (size_t)length < capacity;
}

bool player_slot_store_init(player_slot_store *store, int pref_dirfd, const uint8_t rom_sha256[32],
                            gbb_profile profile, const uint8_t *rom, size_t rom_size) {
    if (store == NULL) return false;
    memset(store, 0, sizeof(*store));
    store->dirfd = -1;
    const char *token = profile_token(profile);
    if (pref_dirfd < 0 || rom_sha256 == NULL || rom == NULL || token == NULL || rom_size == 0u ||
        rom_size > PLAYER_SLOT_MAX_ROM_BYTES)
        return false;
    store->rom = malloc(rom_size);
    if (store->rom == NULL) return false;
    memcpy(store->rom, rom, rom_size);
    store->rom_size = rom_size;
    static const char hex[] = "0123456789abcdef";
    char digest[65];
    for (size_t i = 0u; i < 32u; ++i) {
        digest[2u * i] = hex[rom_sha256[i] >> 4];
        digest[2u * i + 1u] = hex[rom_sha256[i] & 0x0Fu];
    }
    digest[64] = '\0';
    (void)snprintf(store->prefix, sizeof(store->prefix), "%s-%s", digest, token);
    store->dirfd = pref_dirfd;
    store->profile = profile;
    return true;
}

static player_slot_result new_result(player_slot_source source, unsigned slot) {
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.source = source;
    result.slot = slot;
    return result;
}

player_slot_result player_slot_save(player_slot_store *store, const gbb_instance *instance, unsigned slot) {
    player_slot_result result = new_result(PLAYER_SLOT_SOURCE_SLOT, slot);
    result.outcome = PLAYER_SLOT_SAVE_FAILED;
    char name[160];
    if (store == NULL || store->rom == NULL || instance == NULL ||
        !build_name(store, NAME_SLOT, slot, name, sizeof(name)))
        return result;
    size_t size = 0u;
    result.error = (int)gbb_state_size(instance, &size);
    if (result.error != GBB_OK) return result;
    uint8_t *bytes = malloc(size);
    if (bytes == NULL) { result.error = GBB_OUT_OF_MEMORY; return result; }
    result.error = (int)gbb_save_state(instance, bytes, size);
    if (result.error == GBB_OK && host_save_io_replace(store->dirfd, name, bytes, size) == HOST_IO_OK)
        result.outcome = PLAYER_SLOT_SAVED;
    free(bytes);
    return result;
}

/* True when the battery differs from the one recorded right after the last slot load, or no load has
 * happened this session: the in-game save that a load is about to replace has not been backed up. */
static bool battery_differs_from_guard(const player_slot_store *store, const uint8_t *battery, size_t size) {
    return !store->guard_valid || store->guard_size != size || memcmp(store->guard, battery, size) != 0;
}

/* Records the battery right after a load. An allocation failure drops the guard, which only makes the
 * next load write one more preload file. */
static void record_guard(player_slot_store *store, const gbb_instance *instance) {
    free(store->guard);
    store->guard = NULL;
    store->guard_size = 0u;
    store->guard_valid = false;
    size_t size = 0u;
    if (gbb_battery_size(instance, &size) != GBB_OK || size == 0u) {
        store->guard_valid = true; /* nothing to guard on a cartridge without a battery */
        return;
    }
    uint8_t *copy = malloc(size);
    if (copy == NULL || gbb_copy_battery(instance, copy, size) != GBB_OK) {
        free(copy);
        return;
    }
    store->guard = copy;
    store->guard_size = size;
    store->guard_valid = true;
}

/* D-23, all-or-nothing. Each step returns before any later step on failure, and a refusal is found in the
 * scratch instance (step 1a) before the first write, so a refused slot touches no file and no live state. */
player_slot_result player_slot_load(player_slot_store *store, gbb_instance *instance,
                                    player_slot_source source, unsigned slot) {
    player_slot_result result = new_result(source, source == PLAYER_SLOT_SOURCE_UNDO ? 0u : slot);
    result.outcome = PLAYER_SLOT_READ_FAILED;
    char name[160];
    char undo_name[160];
    char preload_name[160];
    if (store == NULL || store->rom == NULL || instance == NULL ||
        !build_name(store, source == PLAYER_SLOT_SOURCE_UNDO ? NAME_UNDO : NAME_SLOT, slot, name, sizeof(name)) ||
        !build_name(store, NAME_UNDO, 0u, undo_name, sizeof(undo_name)) ||
        !build_name(store, NAME_PRELOAD, 0u, preload_name, sizeof(preload_name)))
        return result;

    size_t state_size = 0u;
    result.error = (int)gbb_state_size(instance, &state_size);
    if (result.error != GBB_OK) return result;
    uint8_t *bytes = malloc(state_size + 1u);
    uint8_t *snapshot = malloc(state_size);
    uint8_t *battery = NULL;
    if (bytes == NULL || snapshot == NULL) {
        result.error = GBB_OUT_OF_MEMORY;
        goto done;
    }

    /* Step 1: read at most state size + 1 bytes; one byte too many makes an oversized file a size mismatch. */
    size_t length = 0u;
    const int read_code = host_save_io_read_bounded(store->dirfd, name, bytes, state_size + 1u, &length);
    if (read_code == HOST_IO_EMISSING) {
        result.outcome = source == PLAYER_SLOT_SOURCE_UNDO ? PLAYER_SLOT_NO_UNDO : PLAYER_SLOT_EMPTY;
        goto done;
    }
    if (read_code != HOST_IO_OK) goto done; /* READ_FAILED: symlink, special file, short read or I/O error */

    /* Step 1a: validate in a scratch instance built from the store's own ROM and profile, touching nothing live. */
    {
        gbb_instance *scratch = NULL;
        int error = (int)gbb_create(store->profile, &scratch);
        if (error == GBB_OK) error = (int)gbb_load_rom(scratch, store->rom, store->rom_size);
        if (error == GBB_OK) error = (int)gbb_load_state(scratch, bytes, length);
        gbb_input_clock restored;
        memset(&restored, 0, sizeof(restored));
        restored.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
        if (error == GBB_OK) error = (int)gbb_get_input_clock(scratch, &restored);
        gbb_destroy(scratch);
        if (error != GBB_OK) {
            result.outcome = PLAYER_SLOT_REFUSED;
            result.error = error;
            goto done;
        }
        if (slot_clock_unsafe(&restored)) {
            result.outcome = PLAYER_SLOT_UNSAFE_INPUT;
            goto done;
        }
    }

    /* Step 2: snapshot the live machine in memory. */
    result.error = (int)gbb_save_state(instance, snapshot, state_size);
    if (result.error != GBB_OK) goto done;

    /* Step 3: battery guard. The in-game save about to be replaced is backed up first, atomically. */
    size_t battery_size = 0u;
    if (gbb_battery_size(instance, &battery_size) == GBB_OK && battery_size > 0u) {
        battery = malloc(battery_size);
        if (battery == NULL) {
            result.error = GBB_OUT_OF_MEMORY;
            goto done;
        }
        result.error = (int)gbb_copy_battery(instance, battery, battery_size);
        if (result.error != GBB_OK) goto done;
        const bool needs_preload = battery_differs_from_guard(store, battery, battery_size);
        if (needs_preload && host_save_io_replace(store->dirfd, preload_name, battery, battery_size) != HOST_IO_OK) {
            result.outcome = PLAYER_SLOT_BACKUP_FAILED;
            result.error = GBB_OK;
            goto done;
        }
    }

    /* Step 4: the live load. The scratch instance accepted the same bytes, so a failure here is not
     * expected; gbb_load_state is all-or-nothing, so the live machine is unchanged and the preload file
     * holds the current battery, which is a correct backup. */
    result.error = (int)gbb_load_state(instance, bytes, length);
    if (result.error != GBB_OK) {
        result.outcome = PLAYER_SLOT_REFUSED;
        goto done;
    }

    /* Step 5: the undo snapshot. If it cannot be written, put the machine back. */
    if (host_save_io_replace(store->dirfd, undo_name, snapshot, state_size) != HOST_IO_OK) {
        (void)gbb_load_state(instance, snapshot, state_size);
        result.outcome = PLAYER_SLOT_BACKUP_FAILED;
        result.error = GBB_OK;
        goto done;
    }

    /* Step 6: remember the battery of the loaded state and report the input clock to re-anchor to. */
    record_guard(store, instance);
    result.outcome = source == PLAYER_SLOT_SOURCE_UNDO ? PLAYER_SLOT_UNDONE : PLAYER_SLOT_LOADED;
    result.error = GBB_OK;
    result.clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    (void)gbb_get_input_clock(instance, &result.clock);

done:
    free(battery);
    free(snapshot);
    free(bytes);
    return result;
}

#else /* _WIN32: no store exists; the pure tables below still compile and run. */

bool player_slot_store_init(player_slot_store *store, int pref_dirfd, const uint8_t rom_sha256[32],
                            gbb_profile profile, const uint8_t *rom, size_t rom_size) {
    (void)pref_dirfd;
    (void)rom_sha256;
    (void)profile;
    (void)rom;
    (void)rom_size;
    if (store != NULL) {
        memset(store, 0, sizeof(*store));
        store->dirfd = -1;
    }
    return false;
}

player_slot_result player_slot_save(player_slot_store *store, const gbb_instance *instance, unsigned slot) {
    (void)store;
    (void)instance;
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.outcome = PLAYER_SLOT_SAVE_FAILED;
    result.slot = slot;
    return result;
}

player_slot_result player_slot_load(player_slot_store *store, gbb_instance *instance,
                                    player_slot_source source, unsigned slot) {
    (void)store;
    (void)instance;
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.outcome = PLAYER_SLOT_READ_FAILED;
    result.source = source;
    result.slot = source == PLAYER_SLOT_SOURCE_UNDO ? 0u : slot;
    return result;
}

#endif

/* RED stubs for the pure tables and the selection text: filled in by the next commit. */
player_slot_reanchor player_slot_plan_reanchor(const gbb_input_clock *clock) {
    (void)clock;
    player_slot_reanchor plan;
    memset(&plan, 0, sizeof(plan));
    return plan;
}

player_slot_key_action player_slot_key_decode(const player_slot_key_input *input, unsigned *out_slot) {
    (void)input;
    (void)out_slot;
    return PLAYER_SLOT_KEY_NONE;
}

void player_slot_format_message(const player_slot_result *result, char *out, size_t capacity) {
    (void)result;
    if (out != NULL && capacity > 0u) out[0] = '\0';
}

void player_slot_format_selection(const player_slot_store *store, unsigned slot, char *out, size_t capacity) {
    (void)store;
    (void)slot;
    if (out != NULL && capacity > 0u) out[0] = '\0';
}

void player_slot_format_log(const player_slot_result *result, char *out, size_t capacity) {
    (void)result;
    if (out != NULL && capacity > 0u) out[0] = '\0';
}
