#include "session.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static gbb_instance *create_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

static int run_visible_press(gbb_instance *machine) {
    const gbb_input_event events[] = {
        {8, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {50008, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(machine, events, sizeof(events) / sizeof(events[0])) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 250000, NULL, 0);
    REQUIRE(run.reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 1);
    REQUIRE(gbb_peek_ram(machine, 0xC001) == 1);
    return 0;
}

static bool write_oversized_file(const char *path) {
    uint8_t bytes[32769] = {0};
    FILE *file = fopen(path, "wb");
    if (file == NULL) return false;
    const bool ok = fwrite(bytes, 1, sizeof(bytes), file) == sizeof(bytes);
    return fclose(file) == 0 && ok;
}

static bool write_truncated_file(const char *path) {
    uint8_t bytes[128] = {0};
    FILE *file = fopen(path, "wb");
    if (file == NULL) return false;
    const bool ok = fwrite(bytes, 1, sizeof(bytes), file) == sizeof(bytes);
    return fclose(file) == 0 && ok;
}

static bool write_unsupported_cartridge(const char *path, const char *demo_path) {
    uint8_t rom[32768];
    FILE *source = fopen(demo_path, "rb");
    if (source == NULL) return false;
    const size_t count = fread(rom, 1, sizeof(rom), source);
    const bool source_ok = fclose(source) == 0 && count == sizeof(rom);
    if (!source_ok) return false;
    rom[0x147] = 0x13; /* MBC3 remains outside the current support envelope. */
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    FILE *target = fopen(path, "wb");
    if (target == NULL) return false;
    const bool wrote = fwrite(rom, 1, sizeof(rom), target) == sizeof(rom);
    return fclose(target) == 0 && wrote;
}

static int require_unchanged(gbb_instance *machine, char *current_path,
                             const char *original_path, const char *error) {
    REQUIRE(current_path == original_path);
    REQUIRE(error[0] != '\0');
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 1 && gbb_peek_ram(machine, 0xC001) == 1);
    return 0;
}

static int replacement_failure(const char *demo_path, const char *missing_path) {
    (void)remove(missing_path);
    gbb_instance *machine = create_machine();
    REQUIRE(machine != NULL);
    char *current_path = NULL;
    player_save_identity identity = {0};
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       &identity, error, sizeof(error)));
    REQUIRE(strcmp(current_path, demo_path) == 0);
    REQUIRE(run_visible_press(machine) == 0);

    const char *const original_path = current_path;
    uint8_t pixels[160 * 144];
    gbb_frame_info before;
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), 160, &before) == GBB_OK);
    REQUIRE(write_truncated_file(missing_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "truncated") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);
    gbb_frame_info after;
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), 160, &after) == GBB_OK);
    REQUIRE(after.generation == before.generation &&
            after.completion_half_dots == before.completion_half_dots);

    (void)remove(missing_path);
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    REQUIRE(write_oversized_file(missing_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(error[0] != '\0');
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    REQUIRE(write_unsupported_cartridge(missing_path, demo_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "cartridge type") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);
    free(current_path);
    gbb_destroy(machine);
    remove(missing_path);
    return 0;
}

static int replacement_success(const char *demo_path) {
    gbb_instance *machine = create_machine();
    REQUIRE(machine != NULL);
    char *current_path = NULL;
    player_save_identity identity = {0};
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       &identity, error, sizeof(error)));
    REQUIRE(run_visible_press(machine) == 0);
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       &identity, error, sizeof(error)));
    REQUIRE(strcmp(current_path, demo_path) == 0 && error[0] == '\0');
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 0 && gbb_peek_ram(machine, 0xC001) == 0);
    free(current_path);
    gbb_destroy(machine);
    return 0;
}

#define TEST_ROM_SIZE 32768u
#define TEST_BATTERY_SIZE 8192u
#define TEST_LARGE_BATTERY_SIZE 32768u
#define TEST_SAVE_HEADER 51u
#define TEST_SAVE_MAX_READ 32820u

static bool path_join(char *out, size_t capacity, const char *left,
                      const char *right) {
    const int count = snprintf(out, capacity, "%s/%s", left, right);
    return count >= 0 && (size_t)count < capacity;
}

static void remove_tree(const char *path) {
    struct stat info;
    if (lstat(path, &info) != 0) return;
    if (!S_ISDIR(info.st_mode) || S_ISLNK(info.st_mode)) {
        (void)unlink(path);
        return;
    }
    DIR *directory = opendir(path);
    if (directory != NULL) {
        struct dirent *entry;
        while ((entry = readdir(directory)) != NULL) {
            if (strcmp(entry->d_name, ".") == 0 ||
                strcmp(entry->d_name, "..") == 0) continue;
            char child[4096];
            if (path_join(child, sizeof(child), path, entry->d_name))
                remove_tree(child);
        }
        (void)closedir(directory);
    }
    (void)rmdir(path);
}

static bool start_test_root(const char *root) {
    remove_tree(root);
    if (mkdir(root, 0700) != 0) return false;
    player_session_test_set_pref_path(root);
    player_session_test_set_fault(PLAYER_SESSION_TEST_FAULT_NONE);
    return true;
}

static void fix_test_rom_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void make_test_rom(uint8_t rom[TEST_ROM_SIZE], uint8_t variant) {
    memset(rom, 0, TEST_ROM_SIZE);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    rom[0x200u] = variant;
    fix_test_rom_checksum(rom);
}

static bool write_test_file(const char *path, const uint8_t *bytes,
                            size_t size) {
    const int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd < 0) return false;
    size_t written = 0u;
    while (written < size) {
        const ssize_t count = write(fd, bytes + written, size - written);
        if (count > 0) {
            written += (size_t)count;
            continue;
        }
        if (count < 0 && errno == EINTR) continue;
        (void)close(fd);
        return false;
    }
    return close(fd) == 0;
}

static bool read_test_file(const char *path, uint8_t *bytes, size_t capacity,
                           size_t *out_size) {
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return false;
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0 ||
        (uintmax_t)info.st_size > capacity) {
        (void)close(fd);
        return false;
    }
    size_t total = 0u;
    while (total < (size_t)info.st_size) {
        const ssize_t count = read(fd, bytes + total,
                                   (size_t)info.st_size - total);
        if (count > 0) {
            total += (size_t)count;
            continue;
        }
        if (count < 0 && errno == EINTR) continue;
        (void)close(fd);
        return false;
    }
    if (close(fd) != 0) return false;
    *out_size = total;
    return true;
}

static gbb_instance *new_test_machine(const uint8_t rom[TEST_ROM_SIZE]) {
    gbb_instance *machine = create_machine();
    if (machine == NULL) return NULL;
    if (gbb_load_rom(machine, rom, TEST_ROM_SIZE) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static bool identify_test_rom(const uint8_t rom[TEST_ROM_SIZE],
                              player_save_identity *identity) {
    return player_session_identify_rom(rom, TEST_ROM_SIZE, identity);
}

static char *test_save_path(const player_save_identity *identity) {
    return player_session_test_battery_file_path(identity);
}

static void fill_battery(uint8_t bytes[TEST_BATTERY_SIZE], uint8_t seed) {
    for (size_t i = 0u; i < TEST_BATTERY_SIZE; ++i)
        bytes[i] = (uint8_t)(i * 31u + seed);
}

static bool battery_matches(gbb_instance *machine, const uint8_t *expected,
                            size_t size) {
    uint8_t bytes[TEST_LARGE_BATTERY_SIZE];
    return size <= sizeof(bytes) &&
           gbb_copy_battery(machine, bytes, size) == GBB_OK &&
           memcmp(bytes, expected, size) == 0;
}

static bool setup_saved_state(const char *root, uint8_t variant,
                              uint8_t rom[TEST_ROM_SIZE],
                              gbb_instance **out_machine,
                              player_save_identity *out_identity,
                              char **out_path,
                              uint8_t initial[TEST_BATTERY_SIZE]) {
    (void)root;
    make_test_rom(rom, variant);
    if (!identify_test_rom(rom, out_identity)) return false;
    *out_machine = new_test_machine(rom);
    if (*out_machine == NULL) return false;
    *out_path = test_save_path(out_identity);
    if (*out_path == NULL) return false;
    fill_battery(initial, 0x23u);
    if (gbb_import_battery(*out_machine, initial, TEST_BATTERY_SIZE) != GBB_OK)
        return false;
    char error[256];
    return player_session_save_battery(*out_machine, out_identity,
                                       error, sizeof(error));
}

static bool get_recovery_file(const char *root, unsigned wanted,
                              char *out_path, size_t capacity,
                              uint8_t *bytes, size_t byte_capacity,
                              size_t *out_size) {
    DIR *directory = opendir(root);
    if (directory == NULL) return false;
    unsigned found = 0u;
    bool result = false;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL) {
        if (strstr(entry->d_name, ".recovery-") == NULL) continue;
        if (found++ != wanted) continue;
        if (!path_join(out_path, capacity, root, entry->d_name)) break;
        result = read_test_file(out_path, bytes, byte_capacity, out_size);
        break;
    }
    (void)closedir(directory);
    return result;
}

static unsigned count_recovery_files(const char *root) {
    DIR *directory = opendir(root);
    if (directory == NULL) return 0u;
    unsigned count = 0u;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL)
        if (strstr(entry->d_name, ".recovery-") != NULL) ++count;
    (void)closedir(directory);
    return count;
}

static void remove_temporary_files(const char *root) {
    DIR *directory = opendir(root);
    if (directory == NULL) return;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL) {
        if (strstr(entry->d_name, ".tmp.") == NULL) continue;
        char path[4096];
        if (path_join(path, sizeof(path), root, entry->d_name))
            (void)unlink(path);
    }
    (void)closedir(directory);
}

static unsigned count_temporary_files(const char *root) {
    DIR *directory = opendir(root);
    if (directory == NULL) return 0u;
    unsigned count = 0u;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL)
        if (strstr(entry->d_name, ".tmp.") != NULL) ++count;
    (void)closedir(directory);
    return count;
}

static int session_identity(const char *root) {
    uint8_t rom_a[TEST_ROM_SIZE];
    uint8_t rom_b[TEST_ROM_SIZE];
    make_test_rom(rom_a, 0x10u);
    make_test_rom(rom_b, 0x20u);
    char dir_a[4096], dir_b[4096], path_a[4096], path_b[4096];
    REQUIRE(path_join(dir_a, sizeof(dir_a), root, "a"));
    REQUIRE(path_join(dir_b, sizeof(dir_b), root, "b"));
    REQUIRE(mkdir(dir_a, 0700) == 0 && mkdir(dir_b, 0700) == 0);
    REQUIRE(path_join(path_a, sizeof(path_a), dir_a, "same.gb"));
    REQUIRE(path_join(path_b, sizeof(path_b), dir_b, "same.gb"));
    REQUIRE(write_test_file(path_a, rom_a, sizeof(rom_a)));
    REQUIRE(write_test_file(path_b, rom_a, sizeof(rom_a)));

    gbb_instance *machine = create_machine();
    REQUIRE(machine != NULL);
    char *current_path = NULL;
    player_save_identity first = {0}, moved = {0}, different = {0};
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &current_path, path_a,
                                       &first, error, sizeof(error)));
    char *first_save = test_save_path(&first);
    REQUIRE(first_save != NULL);
    REQUIRE(player_session_replace_rom(machine, &current_path, path_b,
                                       &moved, error, sizeof(error)));
    char *moved_save = test_save_path(&moved);
    REQUIRE(moved_save != NULL);
    REQUIRE(memcmp(first.rom_sha256, moved.rom_sha256, 32u) == 0);
    REQUIRE(strcmp(first_save, moved_save) == 0);
    REQUIRE(strstr(first_save, "-mbc1-03-00002000.gbb") != NULL);

    REQUIRE(write_test_file(path_b, rom_b, sizeof(rom_b)));
    REQUIRE(player_session_replace_rom(machine, &current_path, path_b,
                                       &different, error, sizeof(error)));
    char *different_save = test_save_path(&different);
    REQUIRE(different_save != NULL);
    REQUIRE(memcmp(first.rom_sha256, different.rom_sha256, 32u) != 0);
    REQUIRE(strcmp(first_save, different_save) != 0);

    free(different_save);
    free(moved_save);
    free(first_save);
    free(current_path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_max_size(const char *root) {
    const size_t rom_size = 65536u;
    uint8_t *rom = calloc(rom_size, 1u);
    REQUIRE(rom != NULL);
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x01u;
    rom[0x149u] = 0x03u;
    fix_test_rom_checksum(rom);
    player_save_identity identity = {0};
    REQUIRE(player_session_identify_rom(rom, rom_size, &identity));
    gbb_instance *machine = create_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    char *path = test_save_path(&identity);
    REQUIRE(path != NULL);
    uint8_t *ram = malloc(TEST_LARGE_BATTERY_SIZE);
    REQUIRE(ram != NULL);
    for (size_t i = 0u; i < TEST_LARGE_BATTERY_SIZE; ++i)
        ram[i] = (uint8_t)(i * 13u + 0x39u);
    REQUIRE(gbb_import_battery(machine, ram, TEST_LARGE_BATTERY_SIZE) == GBB_OK);
    char error[256];
    REQUIRE(player_session_save_battery(machine, &identity,
                                        error, sizeof(error)));
    uint8_t max_file[TEST_SAVE_MAX_READ];
    size_t max_size = 0u;
    REQUIRE(read_test_file(path, max_file, sizeof(max_file), &max_size));
    REQUIRE(max_size == 32819u);

    gbb_instance *restored = create_machine();
    REQUIRE(restored != NULL);
    REQUIRE(gbb_load_rom(restored, rom, rom_size) == GBB_OK);
    player_save_identity restored_identity = {0};
    REQUIRE(player_session_identify_rom(rom, rom_size, &restored_identity));
    REQUIRE(player_session_load_battery(restored, &restored_identity,
                                        error, sizeof(error)));
    uint8_t *restored_ram = malloc(TEST_LARGE_BATTERY_SIZE);
    REQUIRE(restored_ram != NULL);
    REQUIRE(gbb_copy_battery(restored, restored_ram,
                             TEST_LARGE_BATTERY_SIZE) == GBB_OK);
    REQUIRE(memcmp(restored_ram, ram, TEST_LARGE_BATTERY_SIZE) == 0);

    uint8_t trailing[TEST_SAVE_MAX_READ];
    memcpy(trailing, max_file, max_size);
    trailing[max_size] = 0xE7u;
    REQUIRE(write_test_file(path, trailing, max_size + 1u));
    gbb_instance *fresh = create_machine();
    REQUIRE(fresh != NULL);
    REQUIRE(gbb_load_rom(fresh, rom, rom_size) == GBB_OK);
    player_save_identity fresh_identity = {0};
    REQUIRE(player_session_identify_rom(rom, rom_size, &fresh_identity));
    REQUIRE(!player_session_load_battery(fresh, &fresh_identity,
                                         error, sizeof(error)));
    REQUIRE(fresh_identity.persistence_enabled);
    REQUIRE(strstr(error, "preserved") != NULL);
    uint8_t *fresh_ram = malloc(TEST_LARGE_BATTERY_SIZE);
    REQUIRE(fresh_ram != NULL);
    REQUIRE(gbb_copy_battery(fresh, fresh_ram,
                             TEST_LARGE_BATTERY_SIZE) == GBB_OK);
    for (size_t i = 0u; i < TEST_LARGE_BATTERY_SIZE; ++i)
        REQUIRE(fresh_ram[i] == 0xFFu);
    char recovery_path[4096];
    uint8_t recovery[TEST_SAVE_MAX_READ];
    size_t recovery_size = 0u;
    REQUIRE(get_recovery_file(root, 0u, recovery_path, sizeof(recovery_path),
                              recovery, sizeof(recovery), &recovery_size));
    REQUIRE(recovery_size == max_size + 1u);
    REQUIRE(memcmp(recovery, trailing, recovery_size) == 0);

    free(fresh_ram);
    gbb_destroy(fresh);
    free(restored_ram);
    gbb_destroy(restored);
    free(ram);
    free(path);
    gbb_destroy(machine);
    free(rom);
    remove_tree(root);
    return 0;
}

static int child_lock_attempt(const player_save_identity *identity,
                              bool expect_busy) {
    const pid_t child = fork();
    if (child < 0) return 1;
    if (child == 0) {
        int lock_fd = -1;
        char error[256];
        const player_session_lock_result result =
            player_session_lock_battery(identity, &lock_fd,
                                        error, sizeof(error));
        if (expect_busy) {
            _exit(result == PLAYER_SESSION_LOCK_BUSY &&
                  strstr(error, "Another GabbaBoy process") != NULL ? 0 : 3);
        }
        if (result != PLAYER_SESSION_LOCK_ACQUIRED) _exit(4);
        player_session_unlock_battery(&lock_fd);
        _exit(0);
    }
    int status = 0;
    if (waitpid(child, &status, 0) != child || !WIFEXITED(status)) return 2;
    return WEXITSTATUS(status);
}

static int session_lock_lifecycle(const char *root) {
    uint8_t rom[TEST_ROM_SIZE];
    make_test_rom(rom, 0x92u);
    player_save_identity identity = {0};
    REQUIRE(identify_test_rom(rom, &identity));
    char *save_path = test_save_path(&identity);
    REQUIRE(save_path != NULL);
    char lock_path[4096];
    const int lock_length = snprintf(lock_path, sizeof(lock_path),
                                     "%s.lock", save_path);
    REQUIRE(lock_length >= 0 && (size_t)lock_length < sizeof(lock_path));
    struct stat info;
    REQUIRE(lstat(save_path, &info) != 0 && errno == ENOENT);
    REQUIRE(lstat(lock_path, &info) != 0 && errno == ENOENT);

    int lock_fd = -1;
    char error[256];
    REQUIRE(player_session_lock_battery(&identity, &lock_fd,
        error, sizeof(error)) == PLAYER_SESSION_LOCK_ACQUIRED);
    REQUIRE(lock_fd >= 0);
    REQUIRE(lstat(lock_path, &info) == 0 && S_ISREG(info.st_mode));
    REQUIRE(lstat(save_path, &info) != 0 && errno == ENOENT);

    int injected_fd = -1;
    player_session_test_set_fault(PLAYER_SESSION_TEST_FAULT_LOCK_ACQUIRE);
    REQUIRE(player_session_lock_battery(&identity, &injected_fd,
        error, sizeof(error)) == PLAYER_SESSION_LOCK_ERROR);
    REQUIRE(injected_fd == -1 && error[0] != '\0');
    REQUIRE(child_lock_attempt(&identity, true) == 0);
    player_session_unlock_battery(&lock_fd);
    REQUIRE(lock_fd == -1);
    REQUIRE(child_lock_attempt(&identity, false) == 0);

    REQUIRE(unlink(lock_path) == 0);
    char sentinel_path[4096];
    REQUIRE(path_join(sentinel_path, sizeof(sentinel_path), root, "lock-target"));
    static const uint8_t sentinel[] = {4u, 5u, 6u};
    REQUIRE(write_test_file(sentinel_path, sentinel, sizeof(sentinel)));
    REQUIRE(symlink(sentinel_path, lock_path) == 0);
    lock_fd = -1;
    REQUIRE(player_session_lock_battery(&identity, &lock_fd,
        error, sizeof(error)) == PLAYER_SESSION_LOCK_ERROR);
    REQUIRE(lock_fd == -1);
    uint8_t sentinel_copy[8];
    size_t sentinel_size = 0u;
    REQUIRE(read_test_file(sentinel_path, sentinel_copy,
                           sizeof(sentinel_copy), &sentinel_size));
    REQUIRE(sentinel_size == sizeof(sentinel));
    REQUIRE(memcmp(sentinel_copy, sentinel, sizeof(sentinel)) == 0);

    char no_battery_root[4096];
    REQUIRE(path_join(no_battery_root, sizeof(no_battery_root), root,
                      "no-battery"));
    REQUIRE(mkdir(no_battery_root, 0700) == 0);
    player_session_test_set_pref_path(no_battery_root);
    uint8_t rom_only[TEST_ROM_SIZE];
    make_test_rom(rom_only, 0u);
    rom_only[0x147u] = 0x00u;
    rom_only[0x149u] = 0x00u;
    fix_test_rom_checksum(rom_only);
    player_save_identity no_battery = {0};
    REQUIRE(identify_test_rom(rom_only, &no_battery));
    REQUIRE(!no_battery.battery_backed);
    lock_fd = -1;
    REQUIRE(player_session_lock_battery(&no_battery, &lock_fd,
        error, sizeof(error)) == PLAYER_SESSION_LOCK_ACQUIRED);
    REQUIRE(lock_fd == -1);
    REQUIRE(test_save_path(&no_battery) == NULL);
    DIR *directory = opendir(no_battery_root);
    REQUIRE(directory != NULL);
    struct dirent *entry;
    unsigned entry_count = 0u;
    while ((entry = readdir(directory)) != NULL)
        if (strcmp(entry->d_name, ".") != 0 &&
            strcmp(entry->d_name, "..") != 0) ++entry_count;
    REQUIRE(closedir(directory) == 0);
    REQUIRE(entry_count == 0u);
    free(save_path);
    remove_tree(root);
    return 0;
}

static int session_save_cadence(void) {
    player_save_cadence cadence = {0};
    player_save_cadence_reset(&cadence, 0u);
    REQUIRE(!player_save_cadence_observe(&cadence, 0u, 0u, 0u));
    REQUIRE(!player_save_cadence_observe(&cadence, 1u, 0u, 0u));
    REQUIRE(!player_save_cadence_observe(&cadence, 1u, 0u,
                                         UINT64_C(1999999999)));
    REQUIRE(player_save_cadence_observe(&cadence, 1u, 0u,
                                        UINT64_C(2000000000)));
    player_save_cadence_reset(&cadence, 1u);
    REQUIRE(!player_save_cadence_observe(&cadence, 2u, 1u, 0u));
    REQUIRE(!player_save_cadence_observe(&cadence, 3u, 1u,
                                         UINT64_C(1000000000)));
    REQUIRE(!player_save_cadence_observe(&cadence, 4u, 1u,
                                         UINT64_C(3000000000)));
    REQUIRE(!player_save_cadence_observe(&cadence, 5u, 1u,
                                         UINT64_C(5000000000)));
    REQUIRE(!player_save_cadence_observe(&cadence, 6u, 1u,
                                         UINT64_C(7000000000)));
    REQUIRE(!player_save_cadence_observe(&cadence, 7u, 1u,
                                         UINT64_C(9000000000)));
    REQUIRE(player_save_cadence_observe(&cadence, 7u, 1u,
                                        UINT64_C(10000000000)));
    REQUIRE(!player_save_cadence_observe(&cadence, 7u, 7u,
                                         UINT64_C(10000000001)));
    REQUIRE(!cadence.dirty);
    return 0;
}

static int session_transition_choices(void) {
    REQUIRE(player_save_transition_resolve(false, false,
        PLAYER_SAVE_TRANSITION_RETRY) == PLAYER_SAVE_TRANSITION_SAVED);
    REQUIRE(player_save_transition_resolve(true, true,
        PLAYER_SAVE_TRANSITION_RETRY) == PLAYER_SAVE_TRANSITION_SAVED);
    REQUIRE(player_save_transition_resolve(true, false,
        PLAYER_SAVE_TRANSITION_RETRY) == PLAYER_SAVE_TRANSITION_WAIT);
    REQUIRE(player_save_transition_resolve(true, false,
        PLAYER_SAVE_TRANSITION_CONTINUE) ==
        PLAYER_SAVE_TRANSITION_CONTINUE_UNSAVED);
    REQUIRE(player_save_transition_resolve(true, false,
        PLAYER_SAVE_TRANSITION_CANCEL) == PLAYER_SAVE_TRANSITION_CANCELLED);
    return 0;
}

static int session_reject_matrix(const char *root) {
    uint8_t rom[TEST_ROM_SIZE];
    uint8_t initial[TEST_BATTERY_SIZE];
    gbb_instance *source = NULL;
    player_save_identity source_identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x35u, rom, &source, &source_identity,
                              &path, initial));
    uint8_t valid[TEST_SAVE_MAX_READ];
    size_t valid_size = 0u;
    REQUIRE(read_test_file(path, valid, sizeof(valid), &valid_size));
    REQUIRE(valid_size == TEST_SAVE_HEADER + TEST_BATTERY_SIZE);
    char collision_path[4096];
    const int collision_length = snprintf(collision_path, sizeof(collision_path),
        "%s.recovery-%ld-%08x", path, (long)getpid(), 1u);
    REQUIRE(collision_length >= 0 &&
            (size_t)collision_length < sizeof(collision_path));
    static const uint8_t collision_bytes[] = {0xC1u, 0xC2u, 0xC3u};
    REQUIRE(write_test_file(collision_path, collision_bytes,
                            sizeof(collision_bytes)));
    static const char *const cases[] = {
        "magic", "version", "digest", "type", "length", "checksum",
        "truncated", "trailing", "oversized"
    };
    unsigned recovered = 0u;
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        uint8_t damaged[TEST_SAVE_MAX_READ + 1u];
        size_t damaged_size = valid_size;
        memcpy(damaged, valid, valid_size);
        if (strcmp(cases[i], "magic") == 0) damaged[0] ^= 0x80u;
        else if (strcmp(cases[i], "version") == 0) damaged[8] = 2u;
        else if (strcmp(cases[i], "digest") == 0) damaged[10] ^= 1u;
        else if (strcmp(cases[i], "type") == 0) damaged[42] = 0x02u;
        else if (strcmp(cases[i], "length") == 0) damaged[43] ^= 1u;
        else if (strcmp(cases[i], "checksum") == 0) damaged[47] ^= 1u;
        else if (strcmp(cases[i], "truncated") == 0) --damaged_size;
        else if (strcmp(cases[i], "trailing") == 0) {
            damaged[damaged_size++] = 0xA7u;
        } else if (strcmp(cases[i], "oversized") == 0) {
            damaged_size = TEST_SAVE_MAX_READ + 1u;
            memset(damaged, 0xD3, damaged_size);
        }
        REQUIRE(write_test_file(path, damaged, damaged_size));
        gbb_instance *machine = new_test_machine(rom);
        REQUIRE(machine != NULL);
        player_save_identity identity = {0};
        REQUIRE(identify_test_rom(rom, &identity));
        char error[256];
        REQUIRE(!player_session_load_battery(machine, &identity,
                                             error, sizeof(error)));
        REQUIRE(strstr(error, "preserved") != NULL);
        REQUIRE(identity.persistence_enabled);
        struct stat target_info;
        REQUIRE(lstat(path, &target_info) != 0 && errno == ENOENT);
        uint8_t battery[TEST_BATTERY_SIZE];
        REQUIRE(gbb_copy_battery(machine, battery, sizeof(battery)) == GBB_OK);
        for (size_t j = 0u; j < sizeof(battery); ++j)
            REQUIRE(battery[j] == 0xFFu);
        char recovery_path[4096];
        uint8_t recovered_bytes[TEST_SAVE_MAX_READ + 1u];
        size_t recovered_size = 0u;
        bool exact_recovery_found = false;
        const unsigned recovery_files = count_recovery_files(root);
        for (unsigned index = 0u; index < recovery_files; ++index) {
            if (get_recovery_file(root, index, recovery_path,
                                  sizeof(recovery_path), recovered_bytes,
                                  sizeof(recovered_bytes), &recovered_size) &&
                recovered_size == damaged_size &&
                memcmp(recovered_bytes, damaged, damaged_size) == 0) {
                exact_recovery_found = true;
                break;
            }
        }
        REQUIRE(exact_recovery_found);
        ++recovered;
        gbb_destroy(machine);
    }
    REQUIRE(count_recovery_files(root) == recovered + 1u);
    uint8_t collision_copy[8];
    size_t collision_size = 0u;
    REQUIRE(read_test_file(collision_path, collision_copy,
                           sizeof(collision_copy), &collision_size));
    REQUIRE(collision_size == sizeof(collision_bytes));
    REQUIRE(memcmp(collision_copy, collision_bytes,
                   sizeof(collision_bytes)) == 0);
    free(path);
    gbb_destroy(source);
    remove_tree(root);
    return 0;
}

static int session_recovery_failure(const char *root) {
    uint8_t rom[TEST_ROM_SIZE], initial[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x45u, rom, &machine, &identity,
                              &path, initial));
    static const uint8_t rejected[] = {0x47u, 0x42u, 0x42u, 0x00u, 0xFFu};
    REQUIRE(write_test_file(path, rejected, sizeof(rejected)));
    identity.saved_generation = 0u;
    player_session_test_set_fault(PLAYER_SESSION_TEST_FAULT_RECOVERY_RENAME);
    char error[256];
    REQUIRE(!player_session_load_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(!identity.persistence_enabled);
    REQUIRE(strstr(error, "could not be preserved") != NULL);
    REQUIRE(battery_matches(machine, initial, sizeof(initial)));
    uint8_t unchanged[16];
    size_t unchanged_size = 0u;
    REQUIRE(read_test_file(path, unchanged, sizeof(unchanged), &unchanged_size));
    REQUIRE(unchanged_size == sizeof(rejected));
    REQUIRE(memcmp(unchanged, rejected, sizeof(rejected)) == 0);
    REQUIRE(count_recovery_files(root) == 0u);
    REQUIRE(!player_session_save_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(strstr(error, "disabled") != NULL);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_recovery_directory_sync_failure(const char *root) {
    uint8_t rom[TEST_ROM_SIZE], initial[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x4Du, rom, &machine, &identity,
                              &path, initial));
    static const uint8_t rejected[] = {0x47u, 0x42u, 0x42u, 0x01u, 0xFAu};
    REQUIRE(write_test_file(path, rejected, sizeof(rejected)));
    player_session_test_set_fault(
        PLAYER_SESSION_TEST_FAULT_DIRECTORY_SYNC);
    char error[256];
    REQUIRE(!player_session_load_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(!identity.persistence_enabled);
    REQUIRE(strstr(error, "could not be preserved") != NULL);
    REQUIRE(battery_matches(machine, initial, sizeof(initial)));
    uint8_t unchanged[16];
    size_t unchanged_size = 0u;
    REQUIRE(read_test_file(path, unchanged, sizeof(unchanged), &unchanged_size));
    REQUIRE(unchanged_size == sizeof(rejected));
    REQUIRE(memcmp(unchanged, rejected, sizeof(rejected)) == 0);
    REQUIRE(count_recovery_files(root) == 0u);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_symlink(const char *root) {
    uint8_t rom[TEST_ROM_SIZE], initial[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x55u, rom, &machine, &identity,
                              &path, initial));
    REQUIRE(unlink(path) == 0);
    char target[4096];
    REQUIRE(path_join(target, sizeof(target), root, "outside.dat"));
    static const uint8_t target_bytes[] = {1u, 2u, 3u, 4u};
    REQUIRE(write_test_file(target, target_bytes, sizeof(target_bytes)));
    REQUIRE(symlink(target, path) == 0);
    char error[256];
    REQUIRE(!player_session_load_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(!identity.persistence_enabled);
    REQUIRE(battery_matches(machine, initial, sizeof(initial)));
    struct stat info;
    REQUIRE(lstat(path, &info) == 0 && S_ISLNK(info.st_mode));
    uint8_t bytes[16];
    size_t size = 0u;
    REQUIRE(read_test_file(target, bytes, sizeof(bytes), &size));
    REQUIRE(size == sizeof(target_bytes));
    REQUIRE(memcmp(bytes, target_bytes, sizeof(target_bytes)) == 0);
    REQUIRE(count_recovery_files(root) == 0u);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_special(const char *root) {
    uint8_t rom[TEST_ROM_SIZE], initial[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x65u, rom, &machine, &identity,
                              &path, initial));
    REQUIRE(unlink(path) == 0);
    REQUIRE(mkfifo(path, 0600) == 0);
    char error[256];
    REQUIRE(!player_session_load_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(!identity.persistence_enabled);
    REQUIRE(battery_matches(machine, initial, sizeof(initial)));
    struct stat info;
    REQUIRE(lstat(path, &info) == 0 && S_ISFIFO(info.st_mode));
    REQUIRE(count_recovery_files(root) == 0u);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_target_type_rejection(const char *root) {
    uint8_t rom[TEST_ROM_SIZE], initial[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, 0x75u, rom, &machine, &identity,
                              &path, initial));
    REQUIRE(unlink(path) == 0);
    char target[4096];
    REQUIRE(path_join(target, sizeof(target), root, "sentinel.dat"));
    static const uint8_t original[] = {9u, 8u, 7u, 6u};
    REQUIRE(write_test_file(target, original, sizeof(original)));
    REQUIRE(symlink(target, path) == 0);
    uint8_t changed[TEST_BATTERY_SIZE];
    fill_battery(changed, 0xA1u);
    REQUIRE(gbb_import_battery(machine, changed, sizeof(changed)) == GBB_OK);
    char error[256];
    REQUIRE(!player_session_save_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(error[0] != '\0');
    struct stat info;
    REQUIRE(lstat(path, &info) == 0 && S_ISLNK(info.st_mode));
    uint8_t bytes[16];
    size_t size = 0u;
    REQUIRE(read_test_file(target, bytes, sizeof(bytes), &size));
    REQUIRE(size == sizeof(original));
    REQUIRE(memcmp(bytes, original, sizeof(original)) == 0);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static bool saved_payload_matches(const char *path,
                                  const uint8_t expected[TEST_BATTERY_SIZE]) {
    uint8_t file[TEST_SAVE_MAX_READ];
    size_t size = 0u;
    if (!read_test_file(path, file, sizeof(file), &size) ||
        size != TEST_SAVE_HEADER + TEST_BATTERY_SIZE ||
        memcmp(file, "GBBBSAVE", 8u) != 0 || file[8] != 1u || file[9] != 0u ||
        file[42] != 0x03u || file[43] != 0x00u || file[44] != 0x20u ||
        file[45] != 0x00u || file[46] != 0x00u ||
        memcmp(file + TEST_SAVE_HEADER, expected, TEST_BATTERY_SIZE) != 0)
        return false;
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (size_t i = TEST_SAVE_HEADER; i < size; ++i) {
        crc ^= file[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ?
                  UINT32_C(0xEDB88320) : 0u);
    }
    crc ^= UINT32_C(0xFFFFFFFF);
    const uint32_t stored_crc = (uint32_t)file[47] |
        ((uint32_t)file[48] << 8) | ((uint32_t)file[49] << 16) |
        ((uint32_t)file[50] << 24);
    return stored_crc == crc;
}

static int session_atomic_failure(const char *root,
                                  player_session_test_fault_stage stage,
                                  bool target_is_new) {
    uint8_t rom[TEST_ROM_SIZE], old_ram[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, (uint8_t)(0x80u + (unsigned)stage),
                              rom, &machine, &identity, &path, old_ram));
    uint8_t old_file[TEST_SAVE_MAX_READ];
    size_t old_file_size = 0u;
    REQUIRE(read_test_file(path, old_file, sizeof(old_file), &old_file_size));
    uint8_t new_ram[TEST_BATTERY_SIZE];
    fill_battery(new_ram, 0xB2u);
    REQUIRE(gbb_import_battery(machine, new_ram, sizeof(new_ram)) == GBB_OK);
    player_session_test_set_fault(stage);
    char error[256];
    REQUIRE(!player_session_save_battery(machine, &identity,
                                         error, sizeof(error)));
    REQUIRE(error[0] != '\0');
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation != identity.saved_generation);
    if (!target_is_new) {
        uint8_t current[TEST_SAVE_MAX_READ];
        size_t current_size = 0u;
        REQUIRE(read_test_file(path, current, sizeof(current), &current_size));
        REQUIRE(current_size == old_file_size);
        REQUIRE(memcmp(current, old_file, old_file_size) == 0);
    } else {
        REQUIRE(saved_payload_matches(path, new_ram));
    }
    REQUIRE(count_temporary_files(root) == 0u);
    remove_temporary_files(root);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

static int session_interrupt(const char *root,
                             player_session_test_fault_stage stage,
                             bool expect_new) {
    uint8_t rom[TEST_ROM_SIZE], old_ram[TEST_BATTERY_SIZE];
    gbb_instance *machine = NULL;
    player_save_identity identity = {0};
    char *path = NULL;
    REQUIRE(setup_saved_state(root, (uint8_t)(0xA0u + (unsigned)stage),
                              rom, &machine, &identity, &path, old_ram));
    uint8_t old_file[TEST_SAVE_MAX_READ];
    size_t old_file_size = 0u;
    REQUIRE(read_test_file(path, old_file, sizeof(old_file), &old_file_size));
    uint8_t new_ram[TEST_BATTERY_SIZE];
    fill_battery(new_ram, 0xC3u);
    REQUIRE(gbb_import_battery(machine, new_ram, sizeof(new_ram)) == GBB_OK);

    const pid_t child = fork();
    REQUIRE(child >= 0);
    if (child == 0) {
        player_session_test_set_fault(stage);
        char error[256];
        const bool saved = player_session_save_battery(
            machine, &identity, error, sizeof(error));
        _exit(saved ? 0 : 2);
    }
    int status = 0;
    REQUIRE(waitpid(child, &status, WUNTRACED) == child);
    if (!WIFSTOPPED(status)) {
        (void)kill(child, SIGKILL);
        (void)waitpid(child, NULL, 0);
        REQUIRE(false);
    }
    REQUIRE(kill(child, SIGKILL) == 0);
    REQUIRE(waitpid(child, &status, 0) == child && WIFSIGNALED(status));

    if (expect_new) {
        REQUIRE(saved_payload_matches(path, new_ram));
        REQUIRE(count_temporary_files(root) == 0u);
    } else {
        uint8_t current[TEST_SAVE_MAX_READ];
        size_t current_size = 0u;
        REQUIRE(read_test_file(path, current, sizeof(current), &current_size));
        REQUIRE(current_size == old_file_size);
        REQUIRE(memcmp(current, old_file, old_file_size) == 0);
        REQUIRE(count_temporary_files(root) == 1u);
    }
    remove_temporary_files(root);
    free(path);
    gbb_destroy(machine);
    remove_tree(root);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 5 || !start_test_root(argv[4])) return 2;
    int result = 2;
    if (strcmp(argv[1], "player_session_replacement_failure") == 0)
        result = replacement_failure(argv[2], argv[3]);
    else if (strcmp(argv[1], "player_session_replacement_success") == 0)
        result = replacement_success(argv[2]);
    else if (strcmp(argv[1], "player_session_identity") == 0)
        result = session_identity(argv[4]);
    else if (strcmp(argv[1], "player_session_lock_lifecycle") == 0)
        result = session_lock_lifecycle(argv[4]);
    else if (strcmp(argv[1], "player_session_save_cadence") == 0)
        result = session_save_cadence();
    else if (strcmp(argv[1], "player_session_transition_choices") == 0)
        result = session_transition_choices();
    else if (strcmp(argv[1], "player_session_max_size") == 0)
        result = session_max_size(argv[4]);
    else if (strcmp(argv[1], "player_session_reject_matrix") == 0)
        result = session_reject_matrix(argv[4]);
    else if (strcmp(argv[1], "player_session_recovery_failure") == 0)
        result = session_recovery_failure(argv[4]);
    else if (strcmp(argv[1], "player_session_recovery_directory_sync_failure") == 0)
        result = session_recovery_directory_sync_failure(argv[4]);
    else if (strcmp(argv[1], "player_session_symlink") == 0)
        result = session_symlink(argv[4]);
    else if (strcmp(argv[1], "player_session_special") == 0)
        result = session_special(argv[4]);
    else if (strcmp(argv[1], "player_session_target_type_rejection") == 0)
        result = session_target_type_rejection(argv[4]);
    else if (strcmp(argv[1], "player_session_temp_create_failure") == 0)
        result = session_atomic_failure(argv[4],
            PLAYER_SESSION_TEST_FAULT_TEMP_CREATE, false);
    else if (strcmp(argv[1], "player_session_short_write_failure") == 0)
        result = session_atomic_failure(argv[4],
            PLAYER_SESSION_TEST_FAULT_SHORT_WRITE, false);
    else if (strcmp(argv[1], "player_session_file_sync_failure") == 0)
        result = session_atomic_failure(argv[4],
            PLAYER_SESSION_TEST_FAULT_FILE_SYNC, false);
    else if (strcmp(argv[1], "player_session_rename_failure") == 0)
        result = session_atomic_failure(argv[4],
            PLAYER_SESSION_TEST_FAULT_RENAME, false);
    else if (strcmp(argv[1], "player_session_directory_sync_failure") == 0)
        result = session_atomic_failure(argv[4],
            PLAYER_SESSION_TEST_FAULT_DIRECTORY_SYNC, true);
    else if (strcmp(argv[1], "player_session_interrupt_before_rename") == 0)
        result = session_interrupt(argv[4],
            PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME, false);
    else if (strcmp(argv[1], "player_session_interrupt_after_rename") == 0)
        result = session_interrupt(argv[4],
            PLAYER_SESSION_TEST_INTERRUPT_AFTER_RENAME, true);
    remove_tree(argv[4]);
    return result;
}
