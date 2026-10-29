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

#ifndef _WIN32

typedef enum { NAME_SLOT, NAME_UNDO } name_kind;

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
    } else {
        length = snprintf(out, capacity, "%s-undo.gbbs", store->prefix);
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

player_slot_result player_slot_load(player_slot_store *store, gbb_instance *instance,
                                    player_slot_source source, unsigned slot) {
    player_slot_result result = new_result(source, source == PLAYER_SLOT_SOURCE_UNDO ? 0u : slot);
    result.outcome = PLAYER_SLOT_READ_FAILED;
    char name[160];
    if (store == NULL || store->rom == NULL || instance == NULL ||
        !build_name(store, source == PLAYER_SLOT_SOURCE_UNDO ? NAME_UNDO : NAME_SLOT, slot, name, sizeof(name)))
        return result;

    /* Read at most state size + 1 bytes: one byte too many is what makes an oversized file a size mismatch. */
    size_t state_size = 0u;
    result.error = (int)gbb_state_size(instance, &state_size);
    if (result.error != GBB_OK) return result;
    uint8_t *bytes = malloc(state_size + 1u);
    if (bytes == NULL) { result.error = GBB_OUT_OF_MEMORY; return result; }
    size_t length = 0u;
    const int read_code = host_save_io_read_bounded(store->dirfd, name, bytes, state_size + 1u, &length);
    if (read_code == HOST_IO_EMISSING) {
        result.outcome = source == PLAYER_SLOT_SOURCE_UNDO ? PLAYER_SLOT_NO_UNDO : PLAYER_SLOT_EMPTY;
    } else if (read_code == HOST_IO_OK) {
        result.error = (int)gbb_load_state(instance, bytes, length);
        if (result.error == GBB_OK) {
            result.outcome = source == PLAYER_SLOT_SOURCE_UNDO ? PLAYER_SLOT_UNDONE : PLAYER_SLOT_LOADED;
            result.clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
            (void)gbb_get_input_clock(instance, &result.clock);
        } else {
            result.outcome = PLAYER_SLOT_REFUSED;
        }
    }
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
