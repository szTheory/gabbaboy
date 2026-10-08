#ifndef GABBABOY_PLAYER_SESSION_H
#define GABBABOY_PLAYER_SESSION_H

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PLAYER_SESSION_PATH_LIMIT 4096u

typedef struct {
    uint8_t rom_sha256[32];
    uint8_t cartridge_type;
    uint32_t ram_size;
    uint64_t saved_generation;
    bool battery_backed;
    bool persistence_enabled;
} player_save_identity;

/* Player save envelope v1 is serialized field-by-field, little-endian: bytes
 * 0..7 magic "GBBBSAVE", 8..9 version 1, 10..41 exact-ROM SHA-256, 42
 * cartridge type, 43..46 RAM length, 47..50 IEEE CRC-32, then exactly the
 * battery RAM payload. The maximum accepted file is 32,819 bytes (51 + 32
 * KiB). The checksum detects accidental corruption and is not authentication.
 * Any future format change must migrate existing progress or retain v1 files. */

/* Replaces both the guest ROM and owned path only after bounded validation succeeds. */
bool player_session_replace_rom(gbb_instance *machine, char **in_out_path,
                                const char *path,
                                player_save_identity *out_identity,
                                char *out_error, size_t error_capacity);
/* Loads a validated, player-managed battery envelope before guest execution.
 * Missing saves keep the core's deterministic fresh-RAM policy. Rejected
 * regular files are preserved under a unique recovery name before fresh RAM
 * is used; unsafe or unpreservable files disable persistence for the session. */
bool player_session_load_battery(gbb_instance *machine,
                                 player_save_identity *identity,
                                 char *out_error, size_t error_capacity);
/* Saves only changed battery RAM through a same-directory atomic replacement. */
bool player_session_save_battery(gbb_instance *machine,
                                 player_save_identity *identity,
                                 char *out_error, size_t error_capacity);
/* Narrow helpers used by the deterministic multi-process player smoke. */
bool player_session_identify_rom(const uint8_t *rom, size_t rom_size,
                                 player_save_identity *out_identity);
void player_session_remove_battery_file(const player_save_identity *identity);

#ifdef GBB_PLAYER_SESSION_TESTING
typedef enum {
    PLAYER_SESSION_TEST_FAULT_NONE = 0,
    PLAYER_SESSION_TEST_FAULT_TEMP_CREATE,
    PLAYER_SESSION_TEST_FAULT_SHORT_WRITE,
    PLAYER_SESSION_TEST_FAULT_FILE_SYNC,
    PLAYER_SESSION_TEST_FAULT_RENAME,
    PLAYER_SESSION_TEST_FAULT_DIRECTORY_SYNC,
    PLAYER_SESSION_TEST_FAULT_RECOVERY_RENAME,
    PLAYER_SESSION_TEST_FAULT_LOCK_ACQUIRE,
    PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME,
    PLAYER_SESSION_TEST_INTERRUPT_AFTER_RENAME
} player_session_test_fault_stage;

/* Narrow test-only controls; production builds do not expose these symbols. */
void player_session_test_set_pref_path(const char *path);
void player_session_test_set_fault(player_session_test_fault_stage stage);
char *player_session_test_battery_file_path(
    const player_save_identity *identity);
#endif

#endif
