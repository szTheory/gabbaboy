/* RED stub: every operation fails until the engine lands in the next commit. */
#include "slots.h"

#include <string.h>

bool player_slot_store_init(player_slot_store *store, int pref_dirfd, const uint8_t rom_sha256[32],
                            gbb_profile profile, const uint8_t *rom, size_t rom_size) {
    (void)pref_dirfd; (void)rom_sha256; (void)profile; (void)rom; (void)rom_size;
    if (store != NULL) memset(store, 0, sizeof(*store));
    return false;
}

void player_slot_store_free(player_slot_store *store) { (void)store; }

player_slot_result player_slot_save(player_slot_store *store, const gbb_instance *instance, unsigned slot) {
    (void)store; (void)instance;
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.outcome = PLAYER_SLOT_SAVE_FAILED;
    result.slot = slot;
    return result;
}

player_slot_result player_slot_load(player_slot_store *store, gbb_instance *instance,
                                    player_slot_source source, unsigned slot) {
    (void)store; (void)instance;
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.outcome = PLAYER_SLOT_READ_FAILED;
    result.slot = slot;
    result.source = source;
    return result;
}
