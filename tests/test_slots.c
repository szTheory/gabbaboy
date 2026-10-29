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
#include <unistd.h>

#define FRAME PLAYER_SLOT_FRAME_HALF_DOTS

static const char *g_case = "?";

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

static bool fx_setup(fixture *fx, gbb_profile profile, uint8_t rom_variant) {
    memset(fx, 0, sizeof(*fx));
    fx->dirfd = -1;
    fx->profile = profile;
    fx->profile_name = profile == GBB_PROFILE_CGB_CPU_E ? "cgb" : "dmg";
    fx->rom = make_rom(rom_variant, &fx->rom_size);
    if (fx->rom == NULL) return false;
    gbb_accept_sha256_hex(fx->rom, fx->rom_size, fx->hex);
    hex_to_digest(fx->hex, fx->digest);
    (void)snprintf(fx->dir, sizeof(fx->dir), "slots-XXXXXX");
    if (mkdtemp(fx->dir) == NULL) return false;
    fx->dirfd = open(fx->dir, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (fx->dirfd < 0) return false;
    fx->store_ready = player_slot_store_init(&fx->store, fx->dirfd, fx->digest, profile, fx->rom, fx->rom_size);
    return fx->store_ready;
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

typedef struct {
    const char *name;
    int (*run)(void);
} slot_case;

static const slot_case g_cases[] = {
    {"roundtrip", case_roundtrip},
    {"empty", case_empty},
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
        return result;
    }
    fprintf(stderr, "unknown case: %s\n", argv[1]);
    return 2;
}
