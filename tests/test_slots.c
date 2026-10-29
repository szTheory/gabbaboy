/* Slot engine tests (Phase 18, D-22..D-26): real files in a temporary pref directory, real instances,
 * public API only. POSIX-only (dir-fd writer, mkdtemp, symlink, utimensat); the portable message, key
 * and re-anchor tables live in test_slots_pure.c.
 *
 * ROMs and states are built at run time: state bytes embed the release token, so none is committed.
 * Every failing check prints "FAIL <case>: file:line expr" and exits 1, so a mutant engine is told
 * apart from a crash. Unknown case names exit 2. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"
#include "gbb_host.h"
#include "slots.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define FRAME PLAYER_SLOT_FRAME_HALF_DOTS

static const char *g_case = "?";
/* The last fixture directory, removed by main even when a REQUIRE returned early (a failing case or a mutant). */
static char g_fixture_dir[64];

#define REQUIRE(x) do { if (!(x)) { \
    printf("FAIL %s: %s:%d %s\n", g_case, __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* ---- ROM and machine helpers ------------------------------------------------------------------- */

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* MBC1+RAM+battery ($03) with 8 KiB of RAM and a 32 KiB ROM: JP $0150, then JR -2 forever, so the CPU
 * runs without touching a device. `variant` goes into the title, which changes the ROM digest. */
static uint8_t *make_rom(uint8_t variant, size_t *out_size) {
    *out_size = 32768u;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x150u] = 0x18u;
    rom[0x151u] = 0xFEu;
    rom[0x134u] = variant;
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    fix_checksum(rom);
    return rom;
}

/* The joypad mirror: the same MBC1+RAM+battery cartridge, but the program enables RAM and then loops
 *   ld a,$10 / ldh ($00),a / ldh a,($00) / ld ($A000),a / jr loop
 * so SRAM byte 0 mirrors the action-button nibble of P1 (bit 0 = A, 0 = pressed). gbb_copy_battery then
 * shows what the guest saw, which is what makes "the press reaches the guest" an observation. */
static uint8_t *make_joypad_rom(size_t *out_size) {
    uint8_t *rom = make_rom('J', out_size);
    if (rom == NULL) return NULL;
    static const uint8_t program[] = {
        0x3E, 0x0A,             /* ld a,$0A      */
        0xEA, 0x00, 0x00,       /* ld ($0000),a  : enable cartridge RAM */
        0x3E, 0x10,             /* loop: ld a,$10  : select the action buttons (bit 5 low) */
        0xE0, 0x00,             /* ldh ($00),a   */
        0xF0, 0x00,             /* ldh a,($00)   */
        0xEA, 0x00, 0xA0,       /* ld ($A000),a  */
        0x18, 0xF5,             /* jr loop       */
    };
    memcpy(rom + 0x150u, program, sizeof(program));
    fix_checksum(rom);
    return rom;
}

static gbb_instance *new_machine(gbb_profile profile, const uint8_t *rom, size_t rom_size) {
    gbb_instance *machine = NULL;
    if (gbb_create(profile, &machine) != GBB_OK) return NULL;
    if (gbb_load_rom(machine, rom, rom_size) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static bool run_frames(gbb_instance *machine, unsigned frames) {
    for (unsigned i = 0u; i < frames; ++i)
        if (gbb_run(machine, FRAME, NULL, 0u).reason != GBB_STOP_BUDGET) return false;
    return true;
}

static uint8_t *state_bytes(const gbb_instance *machine, size_t *out_len) {
    size_t size = 0u;
    if (gbb_state_size(machine, &size) != GBB_OK) return NULL;
    uint8_t *bytes = malloc(size);
    if (bytes == NULL) return NULL;
    if (gbb_save_state(machine, bytes, size) != GBB_OK) {
        free(bytes);
        return NULL;
    }
    *out_len = size;
    return bytes;
}

/* ---- Fixture: a temporary pref directory, a ROM and a store ------------------------------------ */

typedef struct {
    char dir[64];
    int dirfd;
    gbb_profile profile;
    const char *profile_name;
    uint8_t *rom;
    size_t rom_size;
    uint8_t digest[32];
    char hex[65];
    player_slot_store store;
    bool store_ready;
} fixture;

static void hex_to_digest(const char *hex, uint8_t out[32]) {
    for (size_t i = 0u; i < 32u; ++i) {
        unsigned value = 0u;
        (void)sscanf(hex + 2u * i, "%2x", &value);
        out[i] = (uint8_t)value;
    }
}

static void remove_tree(const char *path) {
    DIR *directory = opendir(path);
    if (directory != NULL) {
        struct dirent *entry;
        while ((entry = readdir(directory)) != NULL) {
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) continue;
            char child[512];
            (void)snprintf(child, sizeof(child), "%s/%s", path, entry->d_name);
            struct stat info;
            if (lstat(child, &info) == 0 && S_ISDIR(info.st_mode)) remove_tree(child);
            else (void)unlink(child);
        }
        (void)closedir(directory);
    }
    (void)rmdir(path);
}

/* Takes ownership of `rom` (heap, from make_rom or make_joypad_rom), even on failure. */
static bool fx_setup_rom(fixture *fx, gbb_profile profile, uint8_t *rom, size_t rom_size) {
    memset(fx, 0, sizeof(*fx));
    fx->dirfd = -1;
    fx->profile = profile;
    fx->profile_name = profile == GBB_PROFILE_CGB_CPU_E ? "cgb" : "dmg";
    fx->rom = rom;
    fx->rom_size = rom_size;
    if (fx->rom == NULL) return false;
    gbb_accept_sha256_hex(fx->rom, fx->rom_size, fx->hex);
    hex_to_digest(fx->hex, fx->digest);
    (void)snprintf(fx->dir, sizeof(fx->dir), "slots-XXXXXX");
    if (mkdtemp(fx->dir) == NULL) return false;
    (void)snprintf(g_fixture_dir, sizeof(g_fixture_dir), "%s", fx->dir);
    fx->dirfd = open(fx->dir, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (fx->dirfd < 0) return false;
    fx->store_ready = player_slot_store_init(&fx->store, fx->dirfd, fx->digest, profile, fx->rom, fx->rom_size);
    return fx->store_ready;
}

static bool fx_setup(fixture *fx, gbb_profile profile, uint8_t rom_variant) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(rom_variant, &rom_size);
    return fx_setup_rom(fx, profile, rom, rom_size);
}

static void fx_teardown(fixture *fx) {
    if (fx->store_ready) player_slot_store_free(&fx->store);
    if (fx->dirfd >= 0) (void)close(fx->dirfd);
    if (fx->dir[0] != '\0') remove_tree(fx->dir);
    free(fx->rom);
}

static void slot_file(const fixture *fx, unsigned slot, char out[160]) {
    (void)snprintf(out, 160u, "%s-%s-slot%u.gbbs", fx->hex, fx->profile_name, slot);
}

static uint8_t *read_file(const fixture *fx, const char *name, size_t *out_len) {
    const int fd = openat(fx->dirfd, name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return NULL;
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode)) { (void)close(fd); return NULL; }
    uint8_t *bytes = malloc((size_t)info.st_size + 1u);
    size_t total = 0u;
    while (bytes != NULL && total < (size_t)info.st_size) {
        const ssize_t count = read(fd, bytes + total, (size_t)info.st_size - total);
        if (count <= 0) break;
        total += (size_t)count;
    }
    (void)close(fd);
    if (bytes == NULL || total != (size_t)info.st_size) { free(bytes); return NULL; }
    *out_len = total;
    return bytes;
}

static size_t dir_entry_count(const fixture *fx) {
    const int duplicate = dup(fx->dirfd);
    if (duplicate < 0) return (size_t)-1;
    DIR *directory = fdopendir(duplicate);
    if (directory == NULL) { (void)close(duplicate); return (size_t)-1; }
    rewinddir(directory);
    size_t count = 0u;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL)
        if (strcmp(entry->d_name, ".") != 0 && strcmp(entry->d_name, "..") != 0) ++count;
    (void)closedir(directory);
    return count;
}

/* ---- File helpers ------------------------------------------------------------------------------ */

static void undo_file(const fixture *fx, char out[160]) {
    (void)snprintf(out, 160u, "%s-%s-undo.gbbs", fx->hex, fx->profile_name);
}

static void preload_file(const fixture *fx, char out[160]) {
    (void)snprintf(out, 160u, "%s-%s-battery-preload.bin", fx->hex, fx->profile_name);
}

/* A stand-in for the player's own `.gbb` battery file, which no slot operation may touch. */
static void gbb_file(const fixture *fx, char out[160]) {
    (void)snprintf(out, 160u, "%s.gbb", fx->hex);
}

static bool put_file(const fixture *fx, const char *name, const uint8_t *bytes, size_t length) {
    const int fd = openat(fx->dirfd, name, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return false;
    size_t total = 0u;
    while (total < length) {
        const ssize_t count = write(fd, bytes + total, length - total);
        if (count <= 0) { (void)close(fd); return false; }
        total += (size_t)count;
    }
    return close(fd) == 0;
}

/* "ABSENT", "link:<target>" or the SHA-256 of the contents: the identity a refusal must not change. */
static void file_digest(const fixture *fx, const char *name, char out[80]) {
    struct stat info;
    if (fstatat(fx->dirfd, name, &info, AT_SYMLINK_NOFOLLOW) != 0) {
        (void)snprintf(out, 80u, "ABSENT");
    } else if (S_ISLNK(info.st_mode)) {
        char target[64];
        const ssize_t length = readlinkat(fx->dirfd, name, target, sizeof(target) - 1u);
        target[length < 0 ? 0 : length] = '\0';
        (void)snprintf(out, 80u, "link:%s", target);
    } else if (S_ISREG(info.st_mode)) {
        size_t length = 0u;
        uint8_t *bytes = read_file(fx, name, &length);
        if (bytes == NULL) {
            (void)snprintf(out, 80u, "UNREADABLE");
        } else {
            gbb_accept_sha256_hex(bytes, length, out);
            free(bytes);
        }
    } else {
        (void)snprintf(out, 80u, "OTHER");
    }
}

static uint64_t inode_of(const fixture *fx, const char *name) {
    struct stat info;
    return fstatat(fx->dirfd, name, &info, AT_SYMLINK_NOFOLLOW) == 0 ? (uint64_t)info.st_ino : 0u;
}

/* ---- Live instances and states ----------------------------------------------------------------- */

static void fill_pattern(uint8_t *bytes, size_t size, uint8_t seed) {
    for (size_t i = 0u; i < size; ++i) bytes[i] = (uint8_t)((i * 37u + seed) & 0xFFu);
}

static bool import_pattern(gbb_instance *machine, uint8_t seed) {
    size_t size = 0u;
    if (gbb_battery_size(machine, &size) != GBB_OK) return false;
    uint8_t *bytes = malloc(size);
    if (bytes == NULL) return false;
    fill_pattern(bytes, size, seed);
    const bool ok = gbb_import_battery(machine, bytes, size) == GBB_OK;
    free(bytes);
    return ok;
}

/* A running machine whose battery differs from every fixture state, so a load visibly changes it. */
static gbb_instance *make_live(const fixture *fx, unsigned frames, uint8_t battery_seed) {
    gbb_instance *machine = new_machine(fx->profile, fx->rom, fx->rom_size);
    if (machine == NULL) return NULL;
    if (!run_frames(machine, frames) || !import_pattern(machine, battery_seed)) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static uint8_t *state_of(gbb_profile profile, const uint8_t *rom, size_t rom_size, unsigned frames,
                         uint8_t battery_seed, size_t *out_len) {
    gbb_instance *machine = new_machine(profile, rom, rom_size);
    if (machine == NULL) return NULL;
    uint8_t *bytes = NULL;
    if (run_frames(machine, frames) && import_pattern(machine, battery_seed)) bytes = state_bytes(machine, out_len);
    gbb_destroy(machine);
    return bytes;
}

/* A state whose input queue holds `count` button events, the first at now + first_offset and then one
 * every `stride` half-dots (press A, release A, press A, ...). */
static uint8_t *queued_state(const fixture *fx, unsigned frames, unsigned count, uint64_t first_offset,
                             uint64_t stride, size_t *out_len) {
    gbb_instance *machine = new_machine(fx->profile, fx->rom, fx->rom_size);
    if (machine == NULL) return NULL;
    uint8_t *bytes = NULL;
    gbb_input_event events[64];
    gbb_input_clock clock;
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    if (count <= 64u && run_frames(machine, frames) && gbb_get_input_clock(machine, &clock) == GBB_OK) {
        for (unsigned i = 0u; i < count; ++i) {
            events[i].at_half_dots = clock.now_half_dots + first_offset + i * stride;
            events[i].kind = (i % 2u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE;
            events[i].value = GBB_BUTTON_A;
        }
        if (gbb_queue_events(machine, events, count) == GBB_OK) bytes = state_bytes(machine, out_len);
    }
    gbb_destroy(machine);
    return bytes;
}

/* ---- Observable state: what a refusal must leave byte-identical -------------------------------- */

typedef struct {
    uint8_t *state;
    size_t state_len;
    uint8_t *battery;
    size_t battery_len;
    uint64_t generation;
    char files[4][80]; /* slot under test, undo, preload, .gbb stand-in */
} snapshot;

static bool snap_take(const fixture *fx, const gbb_instance *machine, unsigned slot, snapshot *snap) {
    memset(snap, 0, sizeof(*snap));
    snap->state = state_bytes(machine, &snap->state_len);
    if (snap->state == NULL) return false;
    if (gbb_battery_size(machine, &snap->battery_len) != GBB_OK) return false;
    snap->battery = malloc(snap->battery_len);
    if (snap->battery == NULL || gbb_copy_battery(machine, snap->battery, snap->battery_len) != GBB_OK) return false;
    if (gbb_battery_generation(machine, &snap->generation) != GBB_OK) return false;
    char name[160];
    slot_file(fx, slot, name);
    file_digest(fx, name, snap->files[0]);
    undo_file(fx, name);
    file_digest(fx, name, snap->files[1]);
    preload_file(fx, name);
    file_digest(fx, name, snap->files[2]);
    gbb_file(fx, name);
    file_digest(fx, name, snap->files[3]);
    return true;
}

static void snap_free(snapshot *snap) {
    free(snap->state);
    free(snap->battery);
}

/* Instance bytes: state and battery. The generation and the four files are compared separately. */
static bool snap_machine_equal(const snapshot *a, const snapshot *b) {
    return a->state_len == b->state_len && memcmp(a->state, b->state, a->state_len) == 0 &&
           a->battery_len == b->battery_len && memcmp(a->battery, b->battery, a->battery_len) == 0;
}

static bool snap_files_equal(const snapshot *a, const snapshot *b) {
    for (size_t i = 0u; i < 4u; ++i)
        if (strcmp(a->files[i], b->files[i]) != 0) return false;
    return true;
}

static bool snap_equal(const snapshot *a, const snapshot *b) {
    return snap_machine_equal(a, b) && a->generation == b->generation && snap_files_equal(a, b);
}

/* ---- CRC-32/ISO-HDLC, to re-seal a patched state header ---------------------------------------- */

static uint32_t crc32_update(uint32_t crc, const uint8_t *bytes, size_t length) {
    for (size_t i = 0u; i < length; ++i) {
        crc ^= bytes[i];
        for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return crc;
}

/* The CRC covers header bytes 0..59 and the body; the CRC field at 60 is excluded. */
static uint32_t state_crc(const uint8_t *state, size_t length) {
    uint32_t crc = crc32_update(0xFFFFFFFFu, state, 60u);
    crc = crc32_update(crc, state + 64u, length - 64u);
    return ~crc;
}

static uint32_t read_u32(const uint8_t *bytes) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) | ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

/* ---- Cases ------------------------------------------------------------------------------------- */

static int case_roundtrip(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    gbb_instance *machine = new_machine(fx.profile, fx.rom, fx.rom_size);
    REQUIRE(machine != NULL);
    REQUIRE(run_frames(machine, 30u));

    /* Save slot 3: the file holds exactly the bytes gbb_save_state produced. */
    size_t saved_len = 0u;
    uint8_t *saved = state_bytes(machine, &saved_len);
    REQUIRE(saved != NULL);
    const player_slot_result save = player_slot_save(&fx.store, machine, 3u);
    REQUIRE(save.outcome == PLAYER_SLOT_SAVED);
    char name[160];
    slot_file(&fx, 3u, name);
    size_t file_len = 0u;
    uint8_t *file = read_file(&fx, name, &file_len);
    REQUIRE(file != NULL);
    REQUIRE(file_len == saved_len && memcmp(file, saved, saved_len) == 0);

    /* Run on, so a load has something to undo; then the round trip returns the saved bytes. */
    REQUIRE(run_frames(machine, 60u));
    size_t later_len = 0u;
    uint8_t *later = state_bytes(machine, &later_len);
    REQUIRE(later != NULL && later_len == saved_len && memcmp(later, saved, saved_len) != 0);
    const player_slot_result load = player_slot_load(&fx.store, machine, PLAYER_SLOT_SOURCE_SLOT, 3u);
    REQUIRE(load.outcome == PLAYER_SLOT_LOADED);
    size_t after_len = 0u;
    uint8_t *after = state_bytes(machine, &after_len);
    REQUIRE(after != NULL && after_len == file_len && memcmp(after, file, file_len) == 0);

    free(after);
    free(later);
    free(file);
    free(saved);
    gbb_destroy(machine);
    fx_teardown(&fx);
    return 0;
}

static int case_empty(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    gbb_instance *machine = new_machine(fx.profile, fx.rom, fx.rom_size);
    REQUIRE(machine != NULL);
    REQUIRE(run_frames(machine, 5u));
    size_t before_len = 0u;
    uint8_t *before = state_bytes(machine, &before_len);
    REQUIRE(before != NULL);

    const player_slot_result load = player_slot_load(&fx.store, machine, PLAYER_SLOT_SOURCE_SLOT, 5u);
    REQUIRE(load.outcome == PLAYER_SLOT_EMPTY);
    REQUIRE(dir_entry_count(&fx) == 0u); /* an empty slot writes nothing */
    size_t after_len = 0u;
    uint8_t *after = state_bytes(machine, &after_len);
    REQUIRE(after != NULL && after_len == before_len && memcmp(after, before, before_len) == 0);

    free(after);
    free(before);
    gbb_destroy(machine);
    fx_teardown(&fx);
    return 0;
}

/* Runs the session's load of `slot` and requires the exact outcome and error with every observable
 * unchanged: state, battery, generation, and the slot, undo, preload and .gbb files (D-26 item 2). A file
 * that was missing must stay missing. */
#define CHECK(call) do { if ((call) != 0) return 1; } while (0)

static int expect_untouched_refusal(fixture *fx, gbb_instance *live, unsigned slot,
                                    player_slot_outcome want_outcome, int want_error) {
    char name[160];
    gbb_file(fx, name);
    static const uint8_t standin[] = "stand-in for the player's own battery file";
    REQUIRE(put_file(fx, name, standin, sizeof(standin)));
    snapshot before;
    snapshot after;
    REQUIRE(snap_take(fx, live, slot, &before));
    const player_slot_result result = player_slot_load(&fx->store, live, PLAYER_SLOT_SOURCE_SLOT, slot);
    REQUIRE(result.outcome == want_outcome);
    REQUIRE(result.error == want_error);
    REQUIRE(snap_take(fx, live, slot, &after));
    REQUIRE(snap_equal(&before, &after));
    snap_free(&before);
    snap_free(&after);
    return 0;
}

/* A fixture, a running machine and a valid state for it, shared by the generated refusals. */
typedef struct {
    fixture fx;
    gbb_instance *live;
    uint8_t *good;
    size_t good_len;
} refusal_fixture;

static int refusal_open(refusal_fixture *rf, gbb_profile profile, gbb_profile state_profile) {
    memset(rf, 0, sizeof(*rf));
    REQUIRE(fx_setup(&rf->fx, profile, 'A'));
    rf->live = make_live(&rf->fx, 7u, 0x11u);
    REQUIRE(rf->live != NULL);
    rf->good = state_of(state_profile, rf->fx.rom, rf->fx.rom_size, 20u, 0x22u, &rf->good_len);
    REQUIRE(rf->good != NULL && rf->good_len > 64u);
    return 0;
}

static void refusal_close(refusal_fixture *rf) {
    free(rf->good);
    gbb_destroy(rf->live);
    fx_teardown(&rf->fx);
}

/* Writes `bytes` as slot 1 and requires an untouched REFUSED with `want_error`. */
static int refuse_bytes(refusal_fixture *rf, const uint8_t *bytes, size_t length, int want_error) {
    char name[160];
    slot_file(&rf->fx, 1u, name);
    REQUIRE(put_file(&rf->fx, name, bytes, length));
    return expect_untouched_refusal(&rf->fx, rf->live, 1u, PLAYER_SLOT_REFUSED, want_error);
}

static int case_wrong_rom_untouched(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    /* A valid state of a different game, with undo and preload files already present: all of it stays. */
    size_t rom_size = 0u;
    uint8_t *other_rom = make_rom('B', &rom_size);
    REQUIRE(other_rom != NULL);
    size_t other_len = 0u;
    uint8_t *other = state_of(GBB_PROFILE_DMG_CPU_B, other_rom, rom_size, 20u, 0x22u, &other_len);
    REQUIRE(other != NULL);
    char name[160];
    static const uint8_t undo_marker[] = "existing undo file";
    static const uint8_t preload_marker[] = "existing preload file";
    undo_file(&rf.fx, name);
    REQUIRE(put_file(&rf.fx, name, undo_marker, sizeof(undo_marker)));
    preload_file(&rf.fx, name);
    REQUIRE(put_file(&rf.fx, name, preload_marker, sizeof(preload_marker)));
    CHECK(refuse_bytes(&rf, other, other_len, GBB_STATE_IDENTITY_MISMATCH));
    free(other);
    free(other_rom);
    refusal_close(&rf);
    return 0;
}

static int case_refusal_dmg_in_cgb(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_CGB_CPU_E, GBB_PROFILE_DMG_CPU_B));
    CHECK(refuse_bytes(&rf, rf.good, rf.good_len, GBB_STATE_IDENTITY_MISMATCH));
    refusal_close(&rf);
    return 0;
}

static int case_refusal_version_token(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    /* The local CRC must reproduce the stored one, or the patched file below proves nothing. */
    REQUIRE(state_crc(rf.good, rf.good_len) == read_u32(rf.good + 60u));
    /* Release patch + 1 (u16 at offset 12) with the CRC recomputed: only the version token is wrong. */
    uint8_t *patched = malloc(rf.good_len);
    REQUIRE(patched != NULL);
    memcpy(patched, rf.good, rf.good_len);
    patched[12] = (uint8_t)(patched[12] + 1u);
    const uint32_t crc = state_crc(patched, rf.good_len);
    for (size_t i = 0u; i < 4u; ++i) patched[60u + i] = (uint8_t)(crc >> (8u * i));
    CHECK(refuse_bytes(&rf, patched, rf.good_len, GBB_STATE_UNSUPPORTED_VERSION));
    free(patched);
    refusal_close(&rf);
    return 0;
}

static int case_refusal_text_file(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    char text[300];
    for (size_t i = 0u; i < sizeof(text); ++i) text[i] = "this is a text file, not a state\n"[i % 33u];
    CHECK(refuse_bytes(&rf, (const uint8_t *)text, sizeof(text), GBB_STATE_BAD_FORMAT));
    refusal_close(&rf);
    return 0;
}

static int case_refusal_flipped_byte(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    uint8_t *flipped = malloc(rf.good_len);
    REQUIRE(flipped != NULL);
    memcpy(flipped, rf.good, rf.good_len);
    flipped[64u + 100u] ^= 0x01u; /* one body byte: the CRC no longer matches */
    CHECK(refuse_bytes(&rf, flipped, rf.good_len, GBB_STATE_CORRUPT));
    free(flipped);
    refusal_close(&rf);
    return 0;
}

static int case_refusal_truncated(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    CHECK(refuse_bytes(&rf, rf.good, 100u, GBB_STATE_SIZE_MISMATCH));
    refusal_close(&rf);
    return 0;
}

static int case_refusal_oversize(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    /* size + 4096: the read stops at state size + 1, which is already one byte too many. */
    uint8_t *longer = calloc(rf.good_len + 4096u, 1u);
    REQUIRE(longer != NULL);
    memcpy(longer, rf.good, rf.good_len);
    CHECK(refuse_bytes(&rf, longer, rf.good_len + 4096u, GBB_STATE_SIZE_MISMATCH));
    free(longer);
    refusal_close(&rf);
    return 0;
}

static int case_refusal_symlink(void) {
    refusal_fixture rf;
    CHECK(refusal_open(&rf, GBB_PROFILE_DMG_CPU_B, GBB_PROFILE_DMG_CPU_B));
    /* The link points at a perfectly valid state; following it would have loaded it. */
    REQUIRE(put_file(&rf.fx, "valid-target.bin", rf.good, rf.good_len));
    char name[160];
    slot_file(&rf.fx, 1u, name);
    REQUIRE(symlinkat("valid-target.bin", rf.fx.dirfd, name) == 0);
    CHECK(expect_untouched_refusal(&rf.fx, rf.live, 1u, PLAYER_SLOT_READ_FAILED, GBB_OK));
    refusal_close(&rf);
    return 0;
}

/* Two fixture states of one game: slot 1 holds S1 and slot 2 holds S2, both differing from the live machine. */
typedef struct {
    fixture fx;
    gbb_instance *live;
    uint8_t *s1;
    size_t s1_len;
    uint8_t *s2;
    size_t s2_len;
} pair_fixture;

static int pair_open(pair_fixture *pf) {
    memset(pf, 0, sizeof(*pf));
    REQUIRE(fx_setup(&pf->fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    pf->live = make_live(&pf->fx, 7u, 0x11u);
    REQUIRE(pf->live != NULL);
    pf->s1 = state_of(pf->fx.profile, pf->fx.rom, pf->fx.rom_size, 20u, 0x22u, &pf->s1_len);
    pf->s2 = state_of(pf->fx.profile, pf->fx.rom, pf->fx.rom_size, 30u, 0x33u, &pf->s2_len);
    REQUIRE(pf->s1 != NULL && pf->s2 != NULL);
    char name[160];
    slot_file(&pf->fx, 1u, name);
    REQUIRE(put_file(&pf->fx, name, pf->s1, pf->s1_len));
    slot_file(&pf->fx, 2u, name);
    REQUIRE(put_file(&pf->fx, name, pf->s2, pf->s2_len));
    return 0;
}

static void pair_close(pair_fixture *pf) {
    free(pf->s1);
    free(pf->s2);
    gbb_destroy(pf->live);
    fx_teardown(&pf->fx);
}

static bool live_state_is(const gbb_instance *machine, const uint8_t *want, size_t want_len) {
    size_t length = 0u;
    uint8_t *now = state_bytes(machine, &length);
    const bool same = now != NULL && length == want_len && memcmp(now, want, want_len) == 0;
    free(now);
    return same;
}

static int case_undo_write_failure(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    /* Load 1 succeeds, so the preload guard holds the battery of the loaded state; load 2 therefore writes
     * no preload and the one-shot rename failure lands on the undo write. */
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    snapshot before;
    snapshot after;
    REQUIRE(snap_take(&pf.fx, pf.live, 2u, &before));
    host_save_io_test_fail_next(HOST_IO_ERENAME, EIO);
    const player_slot_result result = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 2u);
    REQUIRE(result.outcome == PLAYER_SLOT_BACKUP_FAILED);
    REQUIRE(snap_take(&pf.fx, pf.live, 2u, &after));
    /* Rolled back: the machine is byte-identical and no file changed. The battery generation is an
     * observer history of the receiving instance and advances with the rollback load, so it is not compared. */
    REQUIRE(snap_machine_equal(&before, &after));
    REQUIRE(snap_files_equal(&before, &after));
    REQUIRE(live_state_is(pf.live, before.state, before.state_len));
    snap_free(&before);
    snap_free(&after);
    pair_close(&pf);
    return 0;
}

/* WR-01. Run only against the fault variants in tests/cmake/slots.cmake, which make the engine's own call fail:
 * the shipped engine cannot be made to refuse a snapshot it just produced, so there is no unmodified run.
 * Both cases need the undo write to fail first (rollback_failure) or the load to succeed (clock_failure). */
static int case_rollback_failure(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    /* Load 1 makes the preload guard hold the loaded battery, so the one-shot rename failure hits the undo write. */
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    host_save_io_test_fail_next(HOST_IO_ERENAME, EIO);
    const player_slot_result result = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 2u);
    /* The rollback was refused, so the machine holds slot 2: "nothing changed" would be false. */
    REQUIRE(result.outcome == PLAYER_SLOT_RESTORE_FAILED);
    REQUIRE(result.error != GBB_OK);
    REQUIRE(live_state_is(pf.live, pf.s2, pf.s2_len));
    char message[160];
    player_slot_format_message(&result, message, sizeof(message));
    REQUIRE(strstr(message, "nothing changed") == NULL);
    pair_close(&pf);
    return 0;
}

static int case_clock_failure(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    const player_slot_result result = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u);
    /* The load applied but the clock could not be read: re-anchoring at time 0 would swallow all input. */
    REQUIRE(result.outcome == PLAYER_SLOT_RESTORE_FAILED);
    REQUIRE(result.error != GBB_OK);
    REQUIRE(result.clock.now_half_dots == 0u);
    REQUIRE(live_state_is(pf.live, pf.s1, pf.s1_len));
    pair_close(&pf);
    return 0;
}

static int case_backup_write_failure(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    /* The session's first load writes the preload first; its failure stops everything before the live load. */
    snapshot before;
    snapshot after;
    REQUIRE(snap_take(&pf.fx, pf.live, 1u, &before));
    host_save_io_test_fail_next(HOST_IO_ERENAME, EIO);
    const player_slot_result result = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u);
    REQUIRE(result.outcome == PLAYER_SLOT_BACKUP_FAILED);
    REQUIRE(snap_take(&pf.fx, pf.live, 1u, &after));
    REQUIRE(snap_equal(&before, &after));
    REQUIRE(strcmp(after.files[1], "ABSENT") == 0); /* no undo file */
    REQUIRE(strcmp(after.files[2], "ABSENT") == 0); /* no preload file either */
    snap_free(&before);
    snap_free(&after);
    pair_close(&pf);
    return 0;
}

static bool exists_nofollow(const fixture *fx, const char *name) {
    struct stat info;
    return fstatat(fx->dirfd, name, &info, AT_SYMLINK_NOFOLLOW) == 0;
}

/* WR-02: attaching a store removes the writer temps a crash left for this ROM and profile, and nothing else. */
static int case_stale_temp_sweep(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    static const uint8_t body[] = "stale";
    char swept[5][200];
    char kept[6][200];
    (void)snprintf(swept[0], sizeof(swept[0]), ".%s-dmg-slot3.gbbs.tmp-111-0", fx.hex);
    (void)snprintf(swept[1], sizeof(swept[1]), ".%s-dmg-undo.gbbs.tmp-111-1", fx.hex);
    (void)snprintf(swept[2], sizeof(swept[2]), ".%s-dmg-battery-preload.bin.tmp-111-0", fx.hex);
    (void)snprintf(swept[3], sizeof(swept[3]), ".%s-dmg-slot9.gbbs.tmp-4242-7", fx.hex);
    (void)snprintf(swept[4], sizeof(swept[4]), ".%s-dmg-slot5.gbbs.tmp-9-0", fx.hex); /* a symlink */
    /* The same ROM under the other profile, another ROM, the player's own battery temp, the real slot, a
     * dot-file without a temp marker, and the symlink's target. */
    (void)snprintf(kept[0], sizeof(kept[0]), ".%s-cgb-slot1.gbbs.tmp-1-0", fx.hex);
    (void)snprintf(kept[1], sizeof(kept[1]), ".%.60sff-dmg-slot3.gbbs.tmp-111-0", fx.hex);
    (void)snprintf(kept[2], sizeof(kept[2]), ".%s.gbb.tmp-5-0", fx.hex);
    (void)snprintf(kept[3], sizeof(kept[3]), "%s-dmg-slot2.gbbs", fx.hex);
    (void)snprintf(kept[4], sizeof(kept[4]), ".%s-dmg-slot4.gbbs", fx.hex);
    (void)snprintf(kept[5], sizeof(kept[5]), "symlink-target.bin");
    for (size_t i = 0u; i < 4u; ++i) REQUIRE(put_file(&fx, swept[i], body, sizeof(body)));
    REQUIRE(symlinkat(kept[5], fx.dirfd, swept[4]) == 0);
    for (size_t i = 0u; i < 6u; ++i) REQUIRE(put_file(&fx, kept[i], body, sizeof(body)));

    player_slot_store_free(&fx.store);
    fx.store_ready = player_slot_store_init(&fx.store, fx.dirfd, fx.digest, fx.profile, fx.rom, fx.rom_size);
    REQUIRE(fx.store_ready);
    for (size_t i = 0u; i < 5u; ++i) REQUIRE(!exists_nofollow(&fx, swept[i]));
    for (size_t i = 0u; i < 6u; ++i) REQUIRE(exists_nofollow(&fx, kept[i])); /* the link's target survives too */
    fx_teardown(&fx);
    return 0;
}

static int case_undo_swap(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    size_t start_len = 0u;
    uint8_t *start = state_bytes(pf.live, &start_len);
    REQUIRE(start != NULL);
    REQUIRE(start_len != pf.s1_len || memcmp(start, pf.s1, start_len) != 0);
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(live_state_is(pf.live, pf.s1, pf.s1_len));
    /* Undo returns to the starting state, and undoing the undo returns to slot 1: a swap. */
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_UNDO, 0u).outcome == PLAYER_SLOT_UNDONE);
    REQUIRE(live_state_is(pf.live, start, start_len));
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_UNDO, 0u).outcome == PLAYER_SLOT_UNDONE);
    REQUIRE(live_state_is(pf.live, pf.s1, pf.s1_len));
    free(start);
    pair_close(&pf);
    return 0;
}

static int case_no_undo(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    gbb_instance *live = make_live(&fx, 7u, 0x11u);
    REQUIRE(live != NULL);
    snapshot before;
    snapshot after;
    REQUIRE(snap_take(&fx, live, 1u, &before));
    const player_slot_result result = player_slot_load(&fx.store, live, PLAYER_SLOT_SOURCE_UNDO, 0u);
    REQUIRE(result.outcome == PLAYER_SLOT_NO_UNDO);
    REQUIRE(snap_take(&fx, live, 1u, &after));
    REQUIRE(snap_equal(&before, &after));
    REQUIRE(dir_entry_count(&fx) == 0u);
    snap_free(&before);
    snap_free(&after);
    gbb_destroy(live);
    fx_teardown(&fx);
    return 0;
}

static bool file_equals(const fixture *fx, const char *name, const uint8_t *want, size_t want_len) {
    size_t length = 0u;
    uint8_t *bytes = read_file(fx, name, &length);
    const bool same = bytes != NULL && length == want_len && memcmp(bytes, want, want_len) == 0;
    free(bytes);
    return same;
}

static bool battery_is(const gbb_instance *machine, const uint8_t *want, size_t want_len) {
    size_t size = 0u;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != want_len) return false;
    uint8_t *bytes = malloc(size);
    const bool same = bytes != NULL && gbb_copy_battery(machine, bytes, size) == GBB_OK &&
                      memcmp(bytes, want, want_len) == 0;
    free(bytes);
    return same;
}

static int case_battery_guard(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    size_t size = 0u;
    REQUIRE(gbb_battery_size(pf.live, &size) == GBB_OK && size == 8192u);
    uint8_t *x = malloc(size);
    uint8_t *y = malloc(size);
    uint8_t *z = malloc(size);
    uint8_t *w = malloc(size);
    REQUIRE(x != NULL && y != NULL && z != NULL && w != NULL);
    REQUIRE(gbb_copy_battery(pf.live, x, size) == GBB_OK); /* the pre-A in-game save */
    fill_pattern(y, size, 0x22u);
    fill_pattern(z, size, 0x33u);
    fill_pattern(w, size, 0x44u);
    char preload[160];
    preload_file(&pf.fx, preload);

    /* Load A (battery Y): the live battery X is backed up first. */
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(battery_is(pf.live, y, size));
    REQUIRE(file_equals(&pf.fx, preload, x, size));
    /* Load B: the live battery Y equals the guard, so no preload write; the pre-A battery X stays. */
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 2u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(battery_is(pf.live, z, size));
    REQUIRE(file_equals(&pf.fx, preload, x, size));
    /* The player saves in game (battery W differs from the guard): the next load backs that up. */
    REQUIRE(gbb_import_battery(pf.live, w, size) == GBB_OK);
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(file_equals(&pf.fx, preload, w, size));

    free(x);
    free(y);
    free(z);
    free(w);
    pair_close(&pf);
    return 0;
}

/* A new player session over the same pref directory: the store is rebuilt, so only what is on disk survives. */
static bool new_session(fixture *fx) {
    player_slot_store_free(&fx->store);
    fx->store_ready = player_slot_store_init(&fx->store, fx->dirfd, fx->digest, fx->profile, fx->rom, fx->rom_size);
    return fx->store_ready;
}

/* WR-03. Session 1 loads a slot over the in-game save X, so the preload file holds X and the battery becomes Y
 * (which the .gbb then keeps). Session 2 starts with Y: its first load must leave the preload at X, because Y is
 * not an in-game save, and a genuine in-game save W made later still has to be backed up. */
static int case_battery_guard_sessions(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    size_t size = 0u;
    REQUIRE(gbb_battery_size(pf.live, &size) == GBB_OK && size == 8192u);
    uint8_t *x = malloc(size);
    uint8_t *w = malloc(size);
    REQUIRE(x != NULL && w != NULL);
    REQUIRE(gbb_copy_battery(pf.live, x, size) == GBB_OK);
    fill_pattern(w, size, 0x44u);
    char preload[160];
    preload_file(&pf.fx, preload);

    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(file_equals(&pf.fx, preload, x, size));

    REQUIRE(new_session(&pf.fx));
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 2u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(file_equals(&pf.fx, preload, x, size)); /* still the real in-game save, not a copy of slot 1's battery */

    REQUIRE(gbb_import_battery(pf.live, w, size) == GBB_OK);
    REQUIRE(new_session(&pf.fx));
    REQUIRE(player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u).outcome == PLAYER_SLOT_LOADED);
    REQUIRE(file_equals(&pf.fx, preload, w, size));

    free(x);
    free(w);
    pair_close(&pf);
    return 0;
}

/* WR-03 follow-up: a guard file that cannot be written still loads, but says the backup is unprotected. A
 * directory at the guard's name makes the rename fail on every POSIX host without a fault seam. */
static int case_guard_write_failure(void) {
    pair_fixture pf;
    CHECK(pair_open(&pf));
    char guard[160];
    (void)snprintf(guard, sizeof(guard), "%s-%s-battery-guard.bin", pf.fx.hex, pf.fx.profile_name);
    REQUIRE(mkdirat(pf.fx.dirfd, guard, 0700) == 0);
    const player_slot_result result = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 1u);
    REQUIRE(result.outcome == PLAYER_SLOT_LOADED);
    REQUIRE(result.guard_unsaved);
    REQUIRE(live_state_is(pf.live, pf.s1, pf.s1_len));
    char message[160];
    player_slot_format_message(&result, message, sizeof(message));
    REQUIRE(strstr(message, "backup may be replaced") != NULL);
    /* With the guard written, the same load carries no warning. */
    REQUIRE(unlinkat(pf.fx.dirfd, guard, AT_REMOVEDIR) == 0);
    const player_slot_result again = player_slot_load(&pf.fx.store, pf.live, PLAYER_SLOT_SOURCE_SLOT, 2u);
    REQUIRE(again.outcome == PLAYER_SLOT_LOADED);
    REQUIRE(!again.guard_unsaved);
    player_slot_format_message(&again, message, sizeof(message));
    REQUIRE(strstr(message, "warning") == NULL);
    pair_close(&pf);
    return 0;
}

static int case_unsafe_queued_input(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    gbb_instance *live = make_live(&fx, 3u, 0x11u);
    REQUIRE(live != NULL);
    /* slot 1: an event 65 frames ahead; slot 2: 60 events (60 + 8 releases > 64); slot 3: 56 events (fits);
     * slot 4: 57 events (one too many). Each is a valid state, so only the input check can refuse it. */
    size_t lengths[4];
    uint8_t *states[4];
    states[0] = queued_state(&fx, 5u, 1u, FRAME * 65u, 0u, &lengths[0]);
    states[1] = queued_state(&fx, 5u, 60u, 1u, 1u, &lengths[1]);
    states[2] = queued_state(&fx, 5u, 56u, 1u, 1u, &lengths[2]);
    states[3] = queued_state(&fx, 5u, 57u, 1u, 1u, &lengths[3]);
    for (unsigned i = 0u; i < 4u; ++i) {
        REQUIRE(states[i] != NULL);
        char name[160];
        slot_file(&fx, i + 1u, name);
        REQUIRE(put_file(&fx, name, states[i], lengths[i]));
    }
    static const unsigned unsafe_slots[] = {1u, 2u, 4u};
    for (size_t i = 0u; i < sizeof(unsafe_slots) / sizeof(unsafe_slots[0]); ++i)
        CHECK(expect_untouched_refusal(&fx, live, unsafe_slots[i], PLAYER_SLOT_UNSAFE_INPUT, GBB_OK));
    /* 56 queued events is the most a load admits, and the live instance now holds them. */
    const player_slot_result result = player_slot_load(&fx.store, live, PLAYER_SLOT_SOURCE_SLOT, 3u);
    REQUIRE(result.outcome == PLAYER_SLOT_LOADED);
    REQUIRE(result.clock.queued_count == 56u);
    for (unsigned i = 0u; i < 4u; ++i) free(states[i]);
    gbb_destroy(live);
    fx_teardown(&fx);
    return 0;
}

static int case_save_failure_keeps_old(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    gbb_instance *first = make_live(&fx, 10u, 0x22u);
    gbb_instance *second = make_live(&fx, 20u, 0x33u);
    REQUIRE(first != NULL && second != NULL);
    REQUIRE(player_slot_save(&fx.store, first, 2u).outcome == PLAYER_SLOT_SAVED);
    char name[160];
    slot_file(&fx, 2u, name);
    size_t old_len = 0u;
    uint8_t *old_bytes = read_file(&fx, name, &old_len);
    REQUIRE(old_bytes != NULL);
    const uint64_t old_inode = inode_of(&fx, name);

    /* The rename fails once: slot 2 keeps its old inode and bytes, and no temp is left behind. */
    host_save_io_test_fail_next(HOST_IO_ERENAME, EIO);
    REQUIRE(player_slot_save(&fx.store, second, 2u).outcome == PLAYER_SLOT_SAVE_FAILED);
    REQUIRE(file_equals(&fx, name, old_bytes, old_len));
    REQUIRE(inode_of(&fx, name) == old_inode);
    REQUIRE(dir_entry_count(&fx) == 1u);
    /* The seam was one-shot: the same save now succeeds and replaces the slot. */
    REQUIRE(player_slot_save(&fx.store, second, 2u).outcome == PLAYER_SLOT_SAVED);
    size_t new_len = 0u;
    uint8_t *new_bytes = state_bytes(second, &new_len);
    REQUIRE(new_bytes != NULL && file_equals(&fx, name, new_bytes, new_len));
    REQUIRE(new_len != old_len || memcmp(new_bytes, old_bytes, old_len) != 0);

    free(new_bytes);
    free(old_bytes);
    gbb_destroy(second);
    gbb_destroy(first);
    fx_teardown(&fx);
    return 0;
}

/* ---- D-24: post-load input admission, observed in the guest ------------------------------------- */

static bool clock_of(const gbb_instance *machine, gbb_input_clock *out) {
    memset(out, 0, sizeof(*out));
    out->struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    return gbb_get_input_clock(machine, out) == GBB_OK;
}

static gbb_input_event button_event(uint64_t at, gbb_input_event_kind kind, gbb_button button) {
    gbb_input_event event;
    memset(&event, 0, sizeof(event));
    event.at_half_dots = at;
    event.kind = kind;
    event.value = (uint8_t)button;
    return event;
}

/* Runs until the instance's own clock reaches `target`, in small steps so the overshoot is a few half-dots. */
static bool run_until(gbb_instance *machine, uint64_t target) {
    gbb_input_clock clock;
    for (unsigned guard = 0u; guard < 100000u; ++guard) {
        if (!clock_of(machine, &clock)) return false;
        if (clock.now_half_dots >= target) return true;
        uint64_t budget = target - clock.now_half_dots;
        if (budget > 2048u) budget = 2048u;
        if (budget < 64u) budget = 64u;
        if (gbb_run(machine, budget, NULL, 0u).reason != GBB_STOP_BUDGET) return false;
    }
    return false;
}

/* SRAM byte 0, bit 0: the A bit of the P1 value the guest last stored (1 = released, 0 = pressed). */
static int guest_sees_a_released(const gbb_instance *machine) {
    size_t size = 0u;
    if (gbb_battery_size(machine, &size) != GBB_OK || size == 0u) return -1;
    uint8_t *bytes = malloc(size);
    if (bytes == NULL || gbb_copy_battery(machine, bytes, size) != GBB_OK) {
        free(bytes);
        return -1;
    }
    const int released = (bytes[0] & 0x01u) != 0u;
    free(bytes);
    return released;
}

/* The shared body of reanchor_later and reanchor_earlier. `result` is the load that just restored `live`.
 * The stale cursor must be refused, the plan's release time accepted, and the press must reach the guest
 * within one frame of its time. The same loaded state run without the press is the control, so the bit
 * that clears is the press and not the program. */
static int check_reanchor(const fixture *fx, gbb_instance *live, const player_slot_result *result,
                          uint64_t stale_cursor, uint32_t want_pending) {
    REQUIRE(result->outcome == PLAYER_SLOT_LOADED);
    gbb_input_clock clock;
    REQUIRE(clock_of(live, &clock));
    REQUIRE(clock.now_half_dots == result->clock.now_half_dots);
    REQUIRE(clock.queued_count == want_pending);
    const player_slot_reanchor plan = player_slot_plan_reanchor(&result->clock);
    REQUIRE(!plan.unsafe);
    REQUIRE(plan.cursor == clock.now_half_dots);
    REQUIRE(plan.pending_count == want_pending);
    REQUIRE(plan.release_at >= clock.now_half_dots);
    REQUIRE(plan.release_at - clock.now_half_dots <= FRAME);
    REQUIRE((plan.release_at > clock.now_half_dots) == (want_pending > 0u));

    /* An event at the player's old cursor, or at now when events were restored, is refused and appends nothing. */
    const gbb_input_event stale = button_event(stale_cursor, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A);
    REQUIRE(gbb_queue_events(live, &stale, 1u) == GBB_INVALID_EVENT);
    REQUIRE(clock_of(live, &clock) && clock.queued_count == want_pending);

    /* The control starts from the loaded state, before any press is queued. */
    size_t loaded_len = 0u;
    uint8_t *loaded = state_bytes(live, &loaded_len);
    REQUIRE(loaded != NULL);
    gbb_instance *control = new_machine(fx->profile, fx->rom, fx->rom_size);
    REQUIRE(control != NULL);
    REQUIRE(gbb_load_state(control, loaded, loaded_len) == GBB_OK);
    free(loaded);
    REQUIRE(guest_sees_a_released(live) == 1); /* before the press the guest sees A released */

    /* The press at release_at is admitted. One frame after its time the guest sees A pressed; the control,
     * which never gets the press, still sees A released. */
    const gbb_input_event press = button_event(plan.release_at, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A);
    REQUIRE(gbb_queue_events(live, &press, 1u) == GBB_OK);
    const uint64_t observe_at = plan.release_at + FRAME;
    REQUIRE(run_until(control, observe_at));
    REQUIRE(guest_sees_a_released(control) == 1);
    REQUIRE(run_until(live, observe_at));
    REQUIRE(guest_sees_a_released(live) == 0);
    gbb_destroy(control);
    return 0;
}

static int case_reanchor_later(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_joypad_rom(&rom_size);
    fixture fx;
    REQUIRE(fx_setup_rom(&fx, GBB_PROFILE_DMG_CPU_B, rom, rom_size));
    gbb_instance *live = new_machine(fx.profile, fx.rom, fx.rom_size);
    gbb_instance *source = new_machine(fx.profile, fx.rom, fx.rom_size);
    REQUIRE(live != NULL && source != NULL);
    REQUIRE(run_frames(live, 3u) && run_frames(source, 8u));
    REQUIRE(player_slot_save(&fx.store, source, 1u).outcome == PLAYER_SLOT_SAVED);

    /* The live machine was at T1; the state is from the later time T2. */
    gbb_input_clock before;
    gbb_input_clock source_clock;
    REQUIRE(clock_of(live, &before) && clock_of(source, &source_clock));
    REQUIRE(before.now_half_dots < source_clock.now_half_dots);
    const player_slot_result result = player_slot_load(&fx.store, live, PLAYER_SLOT_SOURCE_SLOT, 1u);
    REQUIRE(result.clock.now_half_dots == source_clock.now_half_dots);
    CHECK(check_reanchor(&fx, live, &result, before.now_half_dots, 0u));

    gbb_destroy(source);
    gbb_destroy(live);
    fx_teardown(&fx);
    return 0;
}

static int case_reanchor_earlier(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_joypad_rom(&rom_size);
    fixture fx;
    REQUIRE(fx_setup_rom(&fx, GBB_PROFILE_DMG_CPU_B, rom, rom_size));
    gbb_instance *live = new_machine(fx.profile, fx.rom, fx.rom_size);
    gbb_instance *source = new_machine(fx.profile, fx.rom, fx.rom_size);
    REQUIRE(live != NULL && source != NULL);
    REQUIRE(run_frames(live, 9u) && run_frames(source, 4u));

    /* The state is from the earlier time T0 and restores two queued events: a B press and release within
     * the first 2,000 half-dots after its time. */
    gbb_input_clock source_clock;
    REQUIRE(clock_of(source, &source_clock));
    const gbb_input_event restored[2] = {
        button_event(source_clock.now_half_dots + 500u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_B),
        button_event(source_clock.now_half_dots + 1500u, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_B),
    };
    REQUIRE(gbb_queue_events(source, restored, 2u) == GBB_OK);
    REQUIRE(player_slot_save(&fx.store, source, 1u).outcome == PLAYER_SLOT_SAVED);

    gbb_input_clock before;
    REQUIRE(clock_of(live, &before) && before.now_half_dots > source_clock.now_half_dots);
    const player_slot_result result = player_slot_load(&fx.store, live, PLAYER_SLOT_SOURCE_SLOT, 1u);
    REQUIRE(result.outcome == PLAYER_SLOT_LOADED);
    REQUIRE(result.clock.now_half_dots == source_clock.now_half_dots);
    REQUIRE(result.clock.queued_count == 2u);
    REQUIRE(result.clock.last_queued_half_dots == source_clock.now_half_dots + 1500u);
    REQUIRE(player_slot_plan_reanchor(&result.clock).release_at == source_clock.now_half_dots + 1500u);
    /* An event at now precedes the last restored event, so only the plan's release time is accepted. */
    CHECK(check_reanchor(&fx, live, &result, result.clock.now_half_dots, 2u));

    gbb_destroy(source);
    gbb_destroy(live);
    fx_teardown(&fx);
    return 0;
}

static int case_select_message(void) {
    fixture fx;
    REQUIRE(fx_setup(&fx, GBB_PROFILE_DMG_CPU_B, 'A'));
    REQUIRE(setenv("TZ", "UTC", 1) == 0);
    tzset();
    gbb_instance *machine = make_live(&fx, 5u, 0x11u);
    REQUIRE(machine != NULL);
    char message[160];

    player_slot_format_selection(&fx.store, 4u, message, sizeof(message));
    REQUIRE(strcmp(message, "Slot 4 selected: empty") == 0);

    /* A used slot shows its modification time in local time (UTC here): 2026-01-02 03:04. */
    REQUIRE(player_slot_save(&fx.store, machine, 4u).outcome == PLAYER_SLOT_SAVED);
    char name[160];
    slot_file(&fx, 4u, name);
    const struct timespec times[2] = {{(time_t)1767323040, 0}, {(time_t)1767323040, 0}};
    REQUIRE(utimensat(fx.dirfd, name, times, AT_SYMLINK_NOFOLLOW) == 0);
    player_slot_format_selection(&fx.store, 4u, message, sizeof(message));
    REQUIRE(strcmp(message, "Slot 4 selected: saved 2026-01-02 03:04") == 0);

    /* A stat failure other than a missing file reports a bare "saved": the store's descriptor is closed. */
    const int closed = dup(fx.dirfd);
    REQUIRE(closed >= 0);
    player_slot_store broken;
    REQUIRE(player_slot_store_init(&broken, closed, fx.digest, fx.profile, fx.rom, fx.rom_size));
    REQUIRE(close(closed) == 0);
    player_slot_format_selection(&broken, 4u, message, sizeof(message));
    REQUIRE(strcmp(message, "Slot 4 selected: saved") == 0);
    player_slot_store_free(&broken);

    /* Slots outside 1..9 and tiny buffers never overrun. */
    memset(message, 'x', sizeof(message));
    player_slot_format_selection(&fx.store, 0u, message, sizeof(message));
    REQUIRE(message[0] == '\0');
    player_slot_format_selection(&fx.store, 10u, message, sizeof(message));
    REQUIRE(message[0] == '\0');
    char tiny[8];
    memset(tiny, 'x', sizeof(tiny));
    player_slot_format_selection(&fx.store, 4u, tiny, 6u);
    REQUIRE(strcmp(tiny, "Slot ") == 0 && tiny[6] == 'x' && tiny[7] == 'x');

    gbb_destroy(machine);
    fx_teardown(&fx);
    return 0;
}

typedef struct {
    const char *name;
    int (*run)(void);
} slot_case;

static const slot_case g_cases[] = {
    {"roundtrip", case_roundtrip},
    {"empty", case_empty},
    {"wrong_rom_untouched", case_wrong_rom_untouched},
    {"refusal_dmg_in_cgb", case_refusal_dmg_in_cgb},
    {"refusal_version_token", case_refusal_version_token},
    {"refusal_text_file", case_refusal_text_file},
    {"refusal_flipped_byte", case_refusal_flipped_byte},
    {"refusal_truncated", case_refusal_truncated},
    {"refusal_oversize", case_refusal_oversize},
    {"refusal_symlink", case_refusal_symlink},
    {"undo_write_failure", case_undo_write_failure},
    {"backup_write_failure", case_backup_write_failure},
    {"rollback_failure", case_rollback_failure},
    {"clock_failure", case_clock_failure},
    {"stale_temp_sweep", case_stale_temp_sweep},
    {"undo_swap", case_undo_swap},
    {"no_undo", case_no_undo},
    {"battery_guard", case_battery_guard},
    {"battery_guard_sessions", case_battery_guard_sessions},
    {"guard_write_failure", case_guard_write_failure},
    {"unsafe_queued_input", case_unsafe_queued_input},
    {"save_failure_keeps_old", case_save_failure_keeps_old},
    {"reanchor_later", case_reanchor_later},
    {"reanchor_earlier", case_reanchor_earlier},
    {"select_message", case_select_message},
};

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_slots <case>\n");
        return 2;
    }
    for (size_t i = 0u; i < sizeof(g_cases) / sizeof(g_cases[0]); ++i) {
        if (strcmp(argv[1], g_cases[i].name) != 0) continue;
        g_case = g_cases[i].name;
        const int result = g_cases[i].run();
        if (result == 0) printf("PASS %s\n", g_case);
        /* GBB_SLOTS_KEEP=1 keeps the directory of a failing case for inspection. */
        if (g_fixture_dir[0] != '\0' && (result == 0 || getenv("GBB_SLOTS_KEEP") == NULL)) remove_tree(g_fixture_dir);
        return result;
    }
    fprintf(stderr, "unknown case: %s\n", argv[1]);
    return 2;
}
