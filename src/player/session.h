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
    uint32_t ram_size;          /* cartridge RAM bytes, excluding any RTC block */
    uint64_t saved_generation;
    bool battery_backed;
    bool persistence_enabled;
    bool rtc_present;           /* the core exports a clock block after the RAM */
    uint8_t envelope_version;   /* version of the accepted file; 0 when none */
    bool clock_valid;           /* host wall-clock reading handed in by the adapter */
    int64_t clock_now_unix;
    int64_t loaded_saved_at;    /* saved_at of the accepted v2 file; 0 when none */
    bool loaded_saved_valid;    /* the accepted file carried a time stamp */
    bool catch_up_done;         /* the once-per-open catch-up already ran */
} player_save_identity;

typedef enum {
    PLAYER_SESSION_LOCK_ACQUIRED = 0,
    PLAYER_SESSION_LOCK_BUSY,
    PLAYER_SESSION_LOCK_ERROR
} player_session_lock_result;

typedef struct {
    uint64_t observed_generation;
    uint64_t first_dirty_ns;
    uint64_t last_change_ns;
    bool dirty;
} player_save_cadence;

typedef enum {
    PLAYER_SAVE_TRANSITION_WAIT = 0,
    PLAYER_SAVE_TRANSITION_SAVED,
    PLAYER_SAVE_TRANSITION_CONTINUE_UNSAVED,
    PLAYER_SAVE_TRANSITION_CANCELLED
} player_save_transition_result;

typedef enum {
    PLAYER_SAVE_TRANSITION_RETRY = 0,
    PLAYER_SAVE_TRANSITION_CONTINUE,
    PLAYER_SAVE_TRANSITION_CANCEL
} player_save_transition_choice;

/* Player save envelope v2 (every battery type except MBC1 $03 with 8 or 32 KiB
 * RAM, which keeps v1 under its unchanged file name) is a 64-byte
 * little-endian header written field by field: 0..7 magic "GBBBSAVE", 8..9
 * version 2, 10..41 exact-ROM SHA-256, 42 cartridge type, 43 flags (bit 0 RTC
 * block present, bit 1 saved_at valid and only with bit 0, other bits zero),
 * 44..47 RAM length (0, 512, 8192, 32768, 65536 or 131072), 48..51 RTC length
 * (0 or 21), 52..59 signed saved_at in Unix seconds (zero unless flag bit 1),
 * 60..63 IEEE CRC-32 over bytes 0..59 and the payload, then the RAM followed by
 * the RTC block. A file is exactly 64 + RAM + RTC bytes, at most 131,200. The
 * checksum detects accidents and is not authentication. A v1 file is read only
 * for $03; a $03 save read from v2 is written back as v2.
 *
 * Player save envelope v1 is serialized field-by-field, little-endian: bytes
 * 0..7 magic "GBBBSAVE", 8..9 version 1, 10..41 exact-ROM SHA-256, 42
 * cartridge type, 43..46 RAM length, 47..50 IEEE CRC-32, then exactly the
 * battery RAM payload. The maximum accepted file is 32,819 bytes (51 + 32
 * KiB). The checksum detects accidental corruption and is not authentication.
 * Any future format change must migrate existing progress or retain v1 files. */

/* D-26: which profile the session creates. dmg is the default; auto follows the
 * ROM header ($143 bit 7); cgb always uses the CGB profile. */
typedef enum {
    PLAYER_MODEL_DMG = 0,
    PLAYER_MODEL_AUTO,
    PLAYER_MODEL_CGB
} player_model;

/* The one select_profile seam (D-26): reads the ROM with the same bounds as
 * player_session_replace_rom, classifies it with gbb_probe_rom, rejects a PGB
 * header, and picks the profile for the requested model. out_info_flags gets the
 * GBB_INFO_* flags of the chosen profile's probe (GBB_INFO_CGB_ONLY_ON_DMG for a
 * $C0 ROM on the DMG model). It never touches a running instance, and on any
 * failure the out values are left unchanged and out_error says why. */
bool player_session_probe_profile(const char *path, player_model model,
                                  gbb_profile *out_profile,
                                  uint32_t *out_info_flags,
                                  char *out_error, size_t error_capacity);

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
/* The adapter hands the host wall-clock reading to the session before each save;
 * a timer cartridge's v2 file is stamped with it. now_valid false means the
 * clock was unavailable and the file records no save time. */
void player_session_set_clock(player_save_identity *identity, int64_t now_unix,
                              bool now_valid);
/* D-22: advances a timer cartridge's clock once per open, after the battery
 * import and before the first guest instruction. It feeds the loaded file's
 * saved_at and the clock handed to player_session_set_clock to
 * player_catch_up_policy and calls gbb_rtc_catch_up only for APPLY. out_status
 * receives the one-line status (empty when there is nothing to say, such as no
 * timer, no accepted save file, a repeat call, or an unchanged time). Returns
 * false only when the core reports an error. The clock never moves backwards. */
bool player_session_apply_catch_up(gbb_instance *machine,
                                   player_save_identity *identity,
                                   char *out_status, size_t status_capacity);
/* Saves only changed battery RAM through a same-directory atomic replacement. */
bool player_session_save_battery(gbb_instance *machine,
                                 player_save_identity *identity,
                                 char *out_error, size_t error_capacity);
/* The caller holds this advisory lock for the full writable battery session. */
player_session_lock_result player_session_lock_battery(
    const player_save_identity *identity, int *out_lock_fd,
    char *out_error, size_t error_capacity);
void player_session_unlock_battery(int *in_out_lock_fd);
/* Observe host monotonic time and the core generation; due is quiet >=2s or
 * dirty age >=10s. Guest time is never used for save cadence. */
void player_save_cadence_reset(player_save_cadence *cadence,
                               uint64_t generation);
bool player_save_cadence_observe(player_save_cadence *cadence,
                                 uint64_t generation,
                                 uint64_t saved_generation,
                                 uint64_t host_time_ns);
/* Resolve a blocked lifecycle transition without allowing a failed save to
 * proceed unless the user explicitly chooses continue-without-saving. */
player_save_transition_result player_save_transition_resolve(
    bool battery_backed, bool save_succeeded,
    player_save_transition_choice choice);
/* Fills battery status, RAM size and clock presence from the core after a
 * successful gbb_load_rom; the header type byte is never consulted. */
bool player_session_classify_cartridge(gbb_instance *machine,
                                       player_save_identity *identity);
/* Narrow helpers used by the deterministic multi-process player smoke. The
 * identify call fills only the ROM digest and type byte. */
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
