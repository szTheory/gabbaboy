#include "input.h"
#include "script_smoke.h"
#include "session.h"

#include <CommonCrypto/CommonDigest.h>
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

static bool write_sized_file(const char *path, size_t size) {
    uint8_t *bytes = calloc(size, 1u);
    if (bytes == NULL) return false;
    FILE *file = fopen(path, "wb");
    if (file == NULL) {
        free(bytes);
        return false;
    }
    const bool ok = fwrite(bytes, 1, size, file) == size;
    const bool closed = fclose(file) == 0;
    free(bytes);
    return closed && ok;
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
    rom[0x147] = 0x20; /* MBC6 stays unsupported; MBC3 ($13) is supported since Phase 9. */
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

    /* One byte past the 8 MiB bound passes fstat and must hit the read-bound
     * message; two bytes past it is rejected earlier as not bounded. */
    REQUIRE(write_sized_file(missing_path, (size_t)8u * 1024u * 1024u + 1u));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "8 MiB read bound") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);
    REQUIRE(write_sized_file(missing_path, (size_t)8u * 1024u * 1024u + 2u));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "bounded regular file") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    REQUIRE(write_unsupported_cartridge(missing_path, demo_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "cartridge type") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    remove(missing_path);
    REQUIRE(mkfifo(missing_path, 0600) == 0);
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        &identity, error, sizeof(error)));
    REQUIRE(strstr(error, "bounded regular file") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);
    struct stat fifo_info;
    REQUIRE(lstat(missing_path, &fifo_info) == 0 && S_ISFIFO(fifo_info.st_mode));

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
#define PLAYER_SESSION_MAX_IMAGE (131072u + 21u)

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

/* Digest and type come from the ROM bytes; battery status, RAM size and clock
 * presence come from the core, exactly as player_session_replace_rom derives them. */
static bool identify_rom_bytes(const uint8_t *rom, size_t size,
                               player_save_identity *identity) {
    gbb_instance *scratch = create_machine();
    if (scratch == NULL) return false;
    const bool ok = gbb_load_rom(scratch, rom, size) == GBB_OK &&
                    player_session_identify_rom(rom, size, identity) &&
                    player_session_classify_cartridge(scratch, identity);
    gbb_destroy(scratch);
    return ok;
}

static bool identify_test_rom(const uint8_t rom[TEST_ROM_SIZE],
                              player_save_identity *identity) {
    return identify_rom_bytes(rom, TEST_ROM_SIZE, identity);
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
    REQUIRE(identify_rom_bytes(rom, rom_size, &identity));
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
    REQUIRE(identify_rom_bytes(rom, rom_size, &restored_identity));
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
    REQUIRE(identify_rom_bytes(rom, rom_size, &fresh_identity));
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

/* D-36/D-38 session-level script controls. */
typedef struct {
    player_input_state input;
    gbb_instance *machine;
    unsigned calls;
} script_deliver_context;

static bool script_test_deliver(void *context, const gbb_input_event *events, size_t count) {
    script_deliver_context *ctx = context;
    for (size_t i = 0u; i < count; ++i) {
        ctx->calls++;
        const bool pressed = events[i].kind == GBB_INPUT_BUTTON_PRESS;
        const SDL_Scancode scancode = events[i].value == GBB_BUTTON_START
            ? SDL_SCANCODE_RETURN : SDL_SCANCODE_Z;
        if (player_input_key(&ctx->input, ctx->machine, SDL_GetTicksNS(), scancode,
                             pressed, false) != GBB_OK) return false;
    }
    return true;
}

static void script_test_progress(void *context, uint64_t actual_half_dots) {
    script_deliver_context *ctx = context;
    player_input_reconcile(&ctx->input, actual_half_dots);
}

/* The no-input control: the same timeline with no button events must never reach the
 * predicate, so a smoke that cannot fail is caught here without the packaged player. */
static int script_no_input(const char *rom_path, const char *script_path) {
    player_script_smoke smoke;
    char err[192];
    REQUIRE(player_script_smoke_prepare(&smoke, rom_path, script_path, err, sizeof(err)) == 0);
    REQUIRE(smoke.script.event_count == 0u);
    script_deliver_context ctx = {0};
    ctx.machine = create_machine();
    REQUIRE(ctx.machine != NULL);
    REQUIRE(gbb_load_rom(ctx.machine, smoke.rom, smoke.rom_length) == GBB_OK);
    player_input_reset(&ctx.input, SDL_GetTicksNS());
    player_script_smoke_result result;
    REQUIRE(player_script_smoke_run(&smoke, ctx.machine, NULL, script_test_deliver,
                                    script_test_progress, &ctx, &result));
    REQUIRE(result.status != GBB_ACCEPT_DRIVE_HIT);
    REQUIRE(result.status == GBB_ACCEPT_DRIVE_NOT_REACHED);
    REQUIRE(ctx.calls == 0u);
    gbb_destroy(ctx.machine);
    player_script_smoke_release(&smoke);
    return 0;
}

static bool write_filled_file(const char *path, size_t size, uint8_t fill) {
    uint8_t *bytes = malloc(size);
    if (bytes == NULL) return false;
    memset(bytes, fill, size);
    FILE *file = fopen(path, "wb");
    if (file == NULL) {
        free(bytes);
        return false;
    }
    const bool ok = fwrite(bytes, 1, size, file) == size;
    const bool closed = fclose(file) == 0;
    free(bytes);
    return ok && closed;
}

static int require_rejected_untouched(const char *rom_path, const char *script_path) {
    player_script_smoke smoke;
    char err[192] = {0};
    REQUIRE(player_script_smoke_prepare(&smoke, rom_path, script_path, err, sizeof(err)) != 0);
    REQUIRE(err[0] != '\0');
    /* A rejected prepare leaves nothing behind: no script, no ROM bytes, no predicate. */
    REQUIRE(smoke.rom == NULL && smoke.rom_length == 0u && smoke.predicate == NULL);
    REQUIRE(smoke.script.events == NULL && smoke.script.event_count == 0u);
    REQUIRE(smoke.script.marks == NULL && smoke.script.mark_count == 0u);
    return 0;
}

static int script_invalid(const char *libbet_rom, const char *good_script,
                          const char *demo_rom, const char *root) {
    char path[1024];
    /* A NUL byte in an otherwise valid script. */
    snprintf(path, sizeof(path), "%s/nul.input", root);
    FILE *file = fopen(path, "wb");
    REQUIRE(file != NULL);
    static const char nul_script[] = "gbinput 1\nwait 1f\0\n";
    const size_t nul_length = sizeof(nul_script) - 1u; /* drop the literal's own terminator */
    REQUIRE(fwrite(nul_script, 1, nul_length, file) == nul_length && fclose(file) == 0);
    REQUIRE(require_rejected_untouched(libbet_rom, path) == 0);
    /* One byte over the 65536-byte script limit. */
    snprintf(path, sizeof(path), "%s/oversize.input", root);
    REQUIRE(write_filled_file(path, GBB_ACCEPT_SCRIPT_MAX_BYTES + 1u, '\n'));
    REQUIRE(require_rejected_untouched(libbet_rom, path) == 0);
    /* A valid script with a ROM whose digest has no pinned predicate. */
    REQUIRE(require_rejected_untouched(demo_rom, good_script) == 0);
    return 0;
}

/* ---- Envelope v2, v0.1 corpus, classification and ROM cap (Phase 9, D-19..D-26) ---- */

#define V2_HEADER 64u
#define V2_RTC 21u

static uint32_t test_crc32_update(uint32_t finished, const uint8_t *bytes,
                                  size_t size) {
    uint32_t crc = finished ^ UINT32_C(0xFFFFFFFF);
    for (size_t i = 0u; i < size; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static void test_put_u32(uint8_t *out, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i) out[i] = (uint8_t)(value >> (i * 8u));
}

static uint32_t test_get_u32(const uint8_t *in) {
    return (uint32_t)in[0] | ((uint32_t)in[1] << 8) | ((uint32_t)in[2] << 16) |
           ((uint32_t)in[3] << 24);
}

static int64_t test_get_i64(const uint8_t *in) {
    uint64_t bits = 0u;
    for (unsigned i = 0u; i < 8u; ++i) bits |= (uint64_t)in[i] << (i * 8u);
    return (int64_t)bits;
}

/* Recomputes the v2 checksum so a structural mutation is rejected by its own
 * field check and not merely by the checksum. */
static void v2_fix_crc(uint8_t *file, size_t size) {
    if (size < V2_HEADER) return;
    test_put_u32(file + 60u, test_crc32_update(test_crc32_update(0u, file, 60u),
                                               file + V2_HEADER, size - V2_HEADER));
}

/* Builds a synthetic cartridge of `rom_code` banks and `ram_code`. */
static uint8_t *build_cart_rom(uint8_t type, uint8_t rom_code, uint8_t ram_code,
                               uint8_t variant, size_t *out_size) {
    const size_t size = (size_t)32768u << rom_code;
    uint8_t *rom = calloc(size, 1u);
    if (rom == NULL) return NULL;
    rom[0x147u] = type;
    rom[0x148u] = rom_code;
    rom[0x149u] = ram_code;
    rom[0x200u] = variant;
    fix_test_rom_checksum(rom);
    *out_size = size;
    return rom;
}

typedef struct {
    uint8_t *rom;
    size_t rom_size;
    gbb_instance *machine;
    player_save_identity identity;
    uint8_t image[PLAYER_SESSION_MAX_IMAGE];
    size_t image_size;
} cart_case;

static void cart_case_free(cart_case *cart) {
    if (cart->machine != NULL) gbb_destroy(cart->machine);
    free(cart->rom);
    memset(cart, 0, sizeof(*cart));
}

static bool cart_case_open(cart_case *cart, uint8_t type, uint8_t rom_code,
                           uint8_t ram_code, uint8_t variant) {
    memset(cart, 0, sizeof(*cart));
    cart->rom = build_cart_rom(type, rom_code, ram_code, variant, &cart->rom_size);
    cart->machine = create_machine();
    if (cart->rom == NULL || cart->machine == NULL ||
        gbb_load_rom(cart->machine, cart->rom, cart->rom_size) != GBB_OK ||
        !player_session_identify_rom(cart->rom, cart->rom_size, &cart->identity) ||
        !player_session_classify_cartridge(cart->machine, &cart->identity) ||
        !cart->identity.battery_backed ||
        gbb_battery_size(cart->machine, &cart->image_size) != GBB_OK ||
        cart->image_size > sizeof(cart->image) ||
        gbb_copy_battery(cart->machine, cart->image, cart->image_size) != GBB_OK) {
        cart_case_free(cart);
        return false;
    }
    return true;
}

/* Fills the RAM part with a pattern and, for a timer cartridge, gives the
 * block distinct live seconds and minutes so the clock really round-trips. */
static bool cart_case_fill(cart_case *cart, uint8_t seed) {
    const size_t ram = cart->identity.ram_size;
    for (size_t i = 0u; i < ram; ++i) cart->image[i] = (uint8_t)(i * 29u + seed);
    if (cart->identity.rtc_present) {
        cart->image[ram + 9u] = 7u;
        cart->image[ram + 10u] = 3u;
    }
    return gbb_import_battery(cart->machine, cart->image, cart->image_size) == GBB_OK;
}

static bool open_fresh_loaded(const cart_case *source, gbb_instance **out_machine,
                              player_save_identity *out_identity, bool *out_loaded,
                              char *error, size_t error_capacity) {
    *out_machine = create_machine();
    if (*out_machine == NULL ||
        gbb_load_rom(*out_machine, source->rom, source->rom_size) != GBB_OK ||
        !player_session_identify_rom(source->rom, source->rom_size, out_identity) ||
        !player_session_classify_cartridge(*out_machine, out_identity))
        return false;
    *out_loaded = player_session_load_battery(*out_machine, out_identity,
                                              error, error_capacity);
    return true;
}

static bool images_equal(gbb_instance *left, gbb_instance *right, size_t size) {
    uint8_t a[PLAYER_SESSION_MAX_IMAGE], b[PLAYER_SESSION_MAX_IMAGE];
    return size <= sizeof(a) && gbb_copy_battery(left, a, size) == GBB_OK &&
           gbb_copy_battery(right, b, size) == GBB_OK && memcmp(a, b, size) == 0;
}

static int session_v2_max_size(const char *root) {
    cart_case big;
    REQUIRE(cart_case_open(&big, 0x1Bu, 0x00u, 0x04u, 0x11u));
    REQUIRE(big.identity.ram_size == 131072u && !big.identity.rtc_present);
    char *path = test_save_path(&big.identity);
    REQUIRE(path != NULL && strstr(path, "-cart-1b-00020000.gbb") != NULL);
    REQUIRE(cart_case_fill(&big, 0x39u));
    player_session_set_clock(&big.identity, INT64_C(1700000000), true);
    char error[256];
    REQUIRE(player_session_save_battery(big.machine, &big.identity, error, sizeof(error)));
    REQUIRE(big.identity.envelope_version == 2u);
    uint8_t *file = malloc(V2_HEADER + 131072u + 2u);
    REQUIRE(file != NULL);
    size_t size = 0u;
    REQUIRE(read_test_file(path, file, V2_HEADER + 131072u + 2u, &size));
    REQUIRE(size == V2_HEADER + 131072u);
    REQUIRE(memcmp(file, "GBBBSAVE", 8u) == 0 && file[8] == 2u && file[9] == 0u);
    REQUIRE(file[42] == 0x1Bu && file[43] == 0u);
    REQUIRE(test_get_u32(file + 44u) == 131072u && test_get_u32(file + 48u) == 0u);
    REQUIRE(test_get_i64(file + 52u) == 0);
    REQUIRE(memcmp(file + V2_HEADER, big.image, 131072u) == 0);

    /* The identical bytes load back into a fresh instance. */
    gbb_instance *fresh = NULL;
    player_save_identity fresh_identity;
    bool loaded = false;
    REQUIRE(open_fresh_loaded(&big, &fresh, &fresh_identity, &loaded, error, sizeof(error)));
    REQUIRE(loaded && fresh_identity.envelope_version == 2u);
    REQUIRE(images_equal(big.machine, fresh, big.image_size));
    gbb_destroy(fresh);

    /* One byte short and one byte long are rejected, preserved, fresh RAM. */
    for (unsigned variant = 0u; variant < 2u; ++variant) {
        uint8_t *damaged = malloc(size + 1u);
        REQUIRE(damaged != NULL);
        memcpy(damaged, file, size);
        damaged[size] = 0xE7u;
        const size_t damaged_size = variant == 0u ? size - 1u : size + 1u;
        REQUIRE(write_test_file(path, damaged, damaged_size));
        REQUIRE(open_fresh_loaded(&big, &fresh, &fresh_identity, &loaded, error, sizeof(error)));
        REQUIRE(!loaded && strstr(error, "preserved") != NULL);
        REQUIRE(fresh_identity.persistence_enabled && fresh_identity.envelope_version == 0u);
        uint8_t *ram = malloc(131072u);
        REQUIRE(ram != NULL);
        REQUIRE(gbb_copy_battery(fresh, ram, 131072u) == GBB_OK);
        for (size_t i = 0u; i < 131072u; ++i) REQUIRE(ram[i] == 0xFFu);
        free(ram);
        uint8_t *recovery = malloc(V2_HEADER + 131072u + 2u);
        char recovery_path[4096];
        size_t recovery_size = 0u;
        REQUIRE(recovery != NULL);
        REQUIRE(get_recovery_file(root, variant, recovery_path, sizeof(recovery_path),
                                  recovery, V2_HEADER + 131072u + 2u, &recovery_size));
        REQUIRE(recovery_size == damaged_size);
        REQUIRE(memcmp(recovery, damaged, damaged_size) == 0);
        free(recovery);
        free(damaged);
        gbb_destroy(fresh);
    }
    free(file);
    free(path);
    cart_case_free(&big);

    /* A timer cartridge with 8 KiB RAM: 64 + 8192 + 21 bytes, flags 0x03. */
    cart_case timer;
    REQUIRE(cart_case_open(&timer, 0x10u, 0x00u, 0x02u, 0x22u));
    REQUIRE(timer.identity.ram_size == 8192u && timer.identity.rtc_present);
    path = test_save_path(&timer.identity);
    REQUIRE(path != NULL);
    REQUIRE(cart_case_fill(&timer, 0x5Cu));
    player_session_set_clock(&timer.identity, INT64_C(1700000123), true);
    REQUIRE(player_session_save_battery(timer.machine, &timer.identity, error, sizeof(error)));
    uint8_t timer_file[V2_HEADER + 8192u + V2_RTC + 1u];
    REQUIRE(read_test_file(path, timer_file, sizeof(timer_file), &size));
    REQUIRE(size == V2_HEADER + 8192u + V2_RTC);
    REQUIRE(timer_file[43] == 0x03u);
    REQUIRE(test_get_u32(timer_file + 44u) == 8192u && test_get_u32(timer_file + 48u) == V2_RTC);
    REQUIRE(test_get_i64(timer_file + 52u) == INT64_C(1700000123));
    REQUIRE(memcmp(timer_file + V2_HEADER, timer.image, 8192u + V2_RTC) == 0);
    /* Clock unavailable: no stamp and bit 1 clear. */
    player_session_set_clock(&timer.identity, 0, false);
    timer.image[0] ^= 0x01u;
    REQUIRE(gbb_import_battery(timer.machine, timer.image, timer.image_size) == GBB_OK);
    REQUIRE(player_session_save_battery(timer.machine, &timer.identity, error, sizeof(error)));
    REQUIRE(read_test_file(path, timer_file, sizeof(timer_file), &size));
    REQUIRE(timer_file[43] == 0x01u && test_get_i64(timer_file + 52u) == 0);
    free(path);
    cart_case_free(&timer);
    remove_tree(root);
    return 0;
}

typedef struct {
    const char *name;
} v2_mutation;

static int session_v2_reject_matrix(const char *root) {
    cart_case cart;
    REQUIRE(cart_case_open(&cart, 0x10u, 0x00u, 0x02u, 0x33u));
    char *path = test_save_path(&cart.identity);
    REQUIRE(path != NULL);
    REQUIRE(cart_case_fill(&cart, 0x71u));
    player_session_set_clock(&cart.identity, INT64_C(1700000000), true);
    char error[256];
    REQUIRE(player_session_save_battery(cart.machine, &cart.identity, error, sizeof(error)));
    uint8_t valid[V2_HEADER + 8192u + V2_RTC + 2u];
    size_t valid_size = 0u;
    REQUIRE(read_test_file(path, valid, sizeof(valid), &valid_size));
    REQUIRE(valid_size == V2_HEADER + 8192u + V2_RTC);

    gbb_instance *baseline = create_machine();
    REQUIRE(baseline != NULL);
    REQUIRE(gbb_load_rom(baseline, cart.rom, cart.rom_size) == GBB_OK);

    static const char *const names[] = {
        "size-1", "size+1", "version1", "version3", "flags04", "flags07",
        "flags02", "flags00-rtc21", "saved_at-without-bit1", "ram_len100",
        "ram_len4096", "rtc_len0", "rtc_len22", "sha", "type13",
        "crc-payload", "crc-saved_at"
    };
    unsigned expected_recoveries = 0u;
    for (size_t i = 0u; i < sizeof(names) / sizeof(names[0]); ++i) {
        uint8_t damaged[sizeof(valid)];
        size_t size = valid_size;
        memcpy(damaged, valid, valid_size);
        bool fix = true;
        const char *name = names[i];
        if (strcmp(name, "size-1") == 0) { --size; fix = false; }
        else if (strcmp(name, "size+1") == 0) { damaged[size++] = 0xA7u; fix = false; }
        else if (strcmp(name, "version1") == 0) damaged[8] = 1u;
        else if (strcmp(name, "version3") == 0) damaged[8] = 3u;
        else if (strcmp(name, "flags04") == 0) damaged[43] = 0x04u;
        else if (strcmp(name, "flags07") == 0) damaged[43] = 0x07u;
        else if (strcmp(name, "flags02") == 0) damaged[43] = 0x02u;
        else if (strcmp(name, "flags00-rtc21") == 0) damaged[43] = 0x00u;
        else if (strcmp(name, "saved_at-without-bit1") == 0) {
            damaged[43] = 0x01u;
            damaged[52] = 5u;
        } else if (strcmp(name, "ram_len100") == 0) test_put_u32(damaged + 44u, 100u);
        else if (strcmp(name, "ram_len4096") == 0) test_put_u32(damaged + 44u, 4096u);
        else if (strcmp(name, "rtc_len0") == 0) test_put_u32(damaged + 48u, 0u);
        else if (strcmp(name, "rtc_len22") == 0) test_put_u32(damaged + 48u, 22u);
        else if (strcmp(name, "sha") == 0) damaged[10] ^= 1u;
        else if (strcmp(name, "type13") == 0) damaged[42] = 0x13u;
        else if (strcmp(name, "crc-payload") == 0) { damaged[V2_HEADER + 5u] ^= 1u; fix = false; }
        else if (strcmp(name, "crc-saved_at") == 0) { damaged[53] ^= 1u; fix = false; }
        if (fix) v2_fix_crc(damaged, size);
        REQUIRE(write_test_file(path, damaged, size));

        gbb_instance *machine = NULL;
        player_save_identity identity;
        bool loaded = true;
        REQUIRE(open_fresh_loaded(&cart, &machine, &identity, &loaded, error, sizeof(error)));
        if (loaded || strstr(error, "preserved") == NULL) {
            fprintf(stderr, "v2 mutation %s was not rejected and preserved\n", name);
            return 1;
        }
        REQUIRE(identity.persistence_enabled && identity.envelope_version == 0u);
        struct stat info;
        REQUIRE(lstat(path, &info) != 0 && errno == ENOENT);
        REQUIRE(images_equal(machine, baseline, cart.image_size));
        uint64_t generation = 1u;
        REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK && generation == 0u);
        REQUIRE(identity.saved_generation == 0u);
        ++expected_recoveries;
        bool found = false;
        const unsigned count = count_recovery_files(root);
        for (unsigned index = 0u; index < count && !found; ++index) {
            char recovery_path[4096];
            uint8_t recovered[sizeof(valid)];
            size_t recovered_size = 0u;
            found = get_recovery_file(root, index, recovery_path, sizeof(recovery_path),
                                      recovered, sizeof(recovered), &recovered_size) &&
                    recovered_size == size && memcmp(recovered, damaged, size) == 0;
        }
        if (!found) {
            fprintf(stderr, "v2 mutation %s: preserved copy missing\n", name);
            return 1;
        }
        gbb_destroy(machine);
    }
    REQUIRE(count_recovery_files(root) == expected_recoveries);
    gbb_destroy(baseline);
    free(path);
    cart_case_free(&cart);
    remove_tree(root);
    return 0;
}

static bool file_sha256(const char *path, uint8_t out[32]) {
    static uint8_t bytes[V2_HEADER + 131072u + V2_RTC + 1u];
    size_t size = 0u;
    return read_test_file(path, bytes, sizeof(bytes), &size) &&
           CC_SHA256(bytes, (CC_LONG)size, out) != NULL;
}

static bool loads_with_image(const cart_case *source, const uint8_t *expected,
                             size_t size, uint8_t expected_version) {
    gbb_instance *machine = NULL;
    player_save_identity identity;
    bool loaded = false;
    char error[256];
    if (!open_fresh_loaded(source, &machine, &identity, &loaded, error, sizeof(error)))
        return false;
    const bool ok = loaded && identity.envelope_version == expected_version &&
                    battery_matches(machine, expected, size);
    gbb_destroy(machine);
    return ok;
}

static int session_v2_fault(const char *root, player_session_test_fault_stage stage,
                            bool new_file_expected, uint8_t type) {
    cart_case cart;
    const uint8_t ram_code = type == 0x1Bu ? 0x03u : 0x02u;
    REQUIRE(cart_case_open(&cart, type, 0x00u, ram_code, (uint8_t)(0x40u + (unsigned)stage)));
    char *path = test_save_path(&cart.identity);
    REQUIRE(path != NULL);
    REQUIRE(cart_case_fill(&cart, 0x11u));
    player_session_set_clock(&cart.identity, INT64_C(1700000000), true);
    char error[256];
    REQUIRE(player_session_save_battery(cart.machine, &cart.identity, error, sizeof(error)));
    uint8_t old_digest[32];
    REQUIRE(file_sha256(path, old_digest));
    const size_t image_size = cart.image_size;
    uint8_t old_image[PLAYER_SESSION_MAX_IMAGE];
    memcpy(old_image, cart.image, image_size);
    REQUIRE(loads_with_image(&cart, old_image, image_size, 2u));

    REQUIRE(cart_case_fill(&cart, 0xB4u));
    uint8_t new_image[PLAYER_SESSION_MAX_IMAGE];
    REQUIRE(gbb_copy_battery(cart.machine, new_image, image_size) == GBB_OK);
    player_session_set_clock(&cart.identity, INT64_C(1700000999), true);
    const uint64_t saved_before = cart.identity.saved_generation;

    if (stage == PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME ||
        stage == PLAYER_SESSION_TEST_INTERRUPT_AFTER_RENAME) {
        const pid_t child = fork();
        REQUIRE(child >= 0);
        if (child == 0) {
            player_session_test_set_fault(stage);
            char child_error[256];
            _exit(player_session_save_battery(cart.machine, &cart.identity,
                                              child_error, sizeof(child_error)) ? 0 : 2);
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
        REQUIRE(count_temporary_files(root) == (new_file_expected ? 0u : 1u));
    } else {
        player_session_test_set_fault(stage);
        REQUIRE(!player_session_save_battery(cart.machine, &cart.identity,
                                             error, sizeof(error)));
        REQUIRE(error[0] != '\0');
        REQUIRE(cart.identity.saved_generation == saved_before);
        REQUIRE(count_temporary_files(root) == 0u);
    }
    uint8_t current_digest[32];
    REQUIRE(file_sha256(path, current_digest));
    if (new_file_expected) {
        /* The rename happened: the new file is complete and loads. */
        REQUIRE(memcmp(current_digest, old_digest, 32u) != 0);
        REQUIRE(loads_with_image(&cart, new_image, image_size, 2u));
    } else {
        REQUIRE(memcmp(current_digest, old_digest, 32u) == 0);
        REQUIRE(loads_with_image(&cart, old_image, image_size, 2u));
    }
    remove_temporary_files(root);
    free(path);
    cart_case_free(&cart);
    remove_tree(root);
    return 0;
}

/* ---- v0.1 corpus (D-25) ---- */

typedef struct {
    const char *file;
    const char *title;
    uint8_t ram_code;
    size_t ram_size;
} corpus_recipe;

static const corpus_recipe corpus_recipes[] = {
    {"mbc1-8k.gbb", "GBBV1CORPUS8K", 0x02u, 8192u},
    {"mbc1-32k.gbb", "GBBV1CORPUS32K", 0x03u, 32768u}
};

static void corpus_rom(const corpus_recipe *recipe, uint8_t rom[TEST_ROM_SIZE]) {
    memset(rom, 0, TEST_ROM_SIZE);
    memcpy(rom + 0x134u, recipe->title, strlen(recipe->title));
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = recipe->ram_code;
    fix_test_rom_checksum(rom);
}

static void corpus_pattern(uint8_t *out, size_t size) {
    for (size_t i = 0u; i < size; ++i) out[i] = (uint8_t)(i * 37u + 0x31u);
}

/* Loads one corpus envelope in the current player; returns the machine. */
static int corpus_open(const char *fixtures, const corpus_recipe *recipe,
                       const char *rom_path, uint8_t rom[TEST_ROM_SIZE],
                       uint8_t *envelope, size_t *envelope_size,
                       gbb_instance **out_machine, player_save_identity *identity,
                       char **out_path) {
    char corpus_path[4096];
    REQUIRE(path_join(corpus_path, sizeof(corpus_path), fixtures, recipe->file));
    REQUIRE(read_test_file(corpus_path, envelope, 51u + 32768u + 1u, envelope_size));
    REQUIRE(*envelope_size == 51u + recipe->ram_size);
    corpus_rom(recipe, rom);
    uint8_t digest[32];
    REQUIRE(CC_SHA256(rom, TEST_ROM_SIZE, digest) != NULL);
    REQUIRE(memcmp(envelope + 10u, digest, 32u) == 0);
    REQUIRE(write_test_file(rom_path, rom, TEST_ROM_SIZE));
    *out_machine = create_machine();
    REQUIRE(*out_machine != NULL);
    char *owned = NULL;
    char error[256];
    REQUIRE(player_session_replace_rom(*out_machine, &owned, rom_path, identity,
                                       error, sizeof(error)));
    free(owned);
    REQUIRE(identity->ram_size == recipe->ram_size && !identity->rtc_present);
    *out_path = test_save_path(identity);
    REQUIRE(*out_path != NULL && strstr(*out_path, "-mbc1-03-") != NULL);
    REQUIRE(write_test_file(*out_path, envelope, *envelope_size));
    return 0;
}

static int session_v1_corpus_load(const char *root, const char *rom_path,
                                  const char *fixtures) {
    for (size_t i = 0u; i < sizeof(corpus_recipes) / sizeof(corpus_recipes[0]); ++i) {
        uint8_t rom[TEST_ROM_SIZE], envelope[51u + 32768u + 1u];
        size_t envelope_size = 0u;
        gbb_instance *machine = NULL;
        player_save_identity identity;
        char *path = NULL;
        REQUIRE(corpus_open(fixtures, &corpus_recipes[i], rom_path, rom, envelope,
                            &envelope_size, &machine, &identity, &path) == 0);
        char error[256];
        REQUIRE(player_session_load_battery(machine, &identity, error, sizeof(error)));
        REQUIRE(identity.envelope_version == 1u);
        uint8_t expected[32768];
        corpus_pattern(expected, corpus_recipes[i].ram_size);
        REQUIRE(battery_matches(machine, expected, corpus_recipes[i].ram_size));
        /* The corpus file is read, never rewritten, by a load. */
        uint8_t after[51u + 32768u + 1u];
        size_t after_size = 0u;
        REQUIRE(read_test_file(path, after, sizeof(after), &after_size));
        REQUIRE(after_size == envelope_size && memcmp(after, envelope, after_size) == 0);
        free(path);
        gbb_destroy(machine);
        (void)unlink(rom_path);
        remove_tree(root);
        REQUIRE(mkdir(root, 0700) == 0);
    }
    (void)unlink(rom_path);
    remove_tree(root);
    return 0;
}

static int session_v1_mbc1_write_identical(const char *root, const char *rom_path,
                                           const char *fixtures) {
    for (size_t i = 0u; i < sizeof(corpus_recipes) / sizeof(corpus_recipes[0]); ++i) {
        uint8_t rom[TEST_ROM_SIZE], envelope[51u + 32768u + 1u];
        size_t envelope_size = 0u;
        gbb_instance *machine = NULL;
        player_save_identity identity;
        char *path = NULL;
        REQUIRE(corpus_open(fixtures, &corpus_recipes[i], rom_path, rom, envelope,
                            &envelope_size, &machine, &identity, &path) == 0);
        char error[256];
        REQUIRE(player_session_load_battery(machine, &identity, error, sizeof(error)));
        /* Change one byte and change it back: the generation now differs from
         * the saved one while the RAM is the corpus pattern again. */
        uint8_t pattern[32768], changed[32768];
        const size_t ram = corpus_recipes[i].ram_size;
        corpus_pattern(pattern, ram);
        memcpy(changed, pattern, ram);
        changed[0] ^= 0xFFu;
        REQUIRE(gbb_import_battery(machine, changed, ram) == GBB_OK);
        REQUIRE(gbb_import_battery(machine, pattern, ram) == GBB_OK);
        REQUIRE(unlink(path) == 0);
        player_session_set_clock(&identity, INT64_C(1700000000), true);
        REQUIRE(player_session_save_battery(machine, &identity, error, sizeof(error)));
        uint8_t written[51u + 32768u + 1u];
        size_t written_size = 0u;
        REQUIRE(read_test_file(path, written, sizeof(written), &written_size));
        REQUIRE(written_size == envelope_size);
        REQUIRE(memcmp(written, envelope, envelope_size) == 0);
        free(path);
        gbb_destroy(machine);
        (void)unlink(rom_path);
        remove_tree(root);
        REQUIRE(mkdir(root, 0700) == 0);
    }
    (void)unlink(rom_path);
    remove_tree(root);
    return 0;
}

/* A $03 save that was read from v2 is written back as v2, never as v1. */
static int session_v1_v2_stickiness(const char *root) {
    cart_case cart;
    REQUIRE(cart_case_open(&cart, 0x03u, 0x00u, 0x02u, 0x61u));
    char *path = test_save_path(&cart.identity);
    REQUIRE(path != NULL && strstr(path, "-mbc1-03-00002000.gbb") != NULL);
    REQUIRE(cart_case_fill(&cart, 0x2Au));
    char error[256];
    REQUIRE(player_session_save_battery(cart.machine, &cart.identity, error, sizeof(error)));
    uint8_t file[V2_HEADER + 8192u + 1u];
    size_t size = 0u;
    REQUIRE(read_test_file(path, file, sizeof(file), &size));
    REQUIRE(size == 51u + 8192u && file[8] == 1u);
    /* Hand-build the v2 form of the same save. */
    uint8_t v2[V2_HEADER + 8192u];
    memset(v2, 0, V2_HEADER);
    memcpy(v2, "GBBBSAVE", 8u);
    v2[8] = 2u;
    memcpy(v2 + 10u, cart.identity.rom_sha256, 32u);
    v2[42] = 0x03u;
    test_put_u32(v2 + 44u, 8192u);
    memcpy(v2 + V2_HEADER, cart.image, 8192u);
    v2_fix_crc(v2, sizeof(v2));
    REQUIRE(write_test_file(path, v2, sizeof(v2)));
    gbb_instance *machine = NULL;
    player_save_identity identity;
    bool loaded = false;
    REQUIRE(open_fresh_loaded(&cart, &machine, &identity, &loaded, error, sizeof(error)));
    REQUIRE(loaded && identity.envelope_version == 2u);
    REQUIRE(battery_matches(machine, cart.image, 8192u));
    cart.image[1] ^= 0x10u;
    REQUIRE(gbb_import_battery(machine, cart.image, 8192u) == GBB_OK);
    REQUIRE(player_session_save_battery(machine, &identity, error, sizeof(error)));
    REQUIRE(read_test_file(path, file, sizeof(file), &size));
    REQUIRE(size == V2_HEADER + 8192u && file[8] == 2u);
    /* Saving again without a change writes nothing (idempotent). */
    uint8_t digest_a[32], digest_b[32];
    REQUIRE(file_sha256(path, digest_a));
    REQUIRE(unlink(path) == 0);
    REQUIRE(player_session_save_battery(machine, &identity, error, sizeof(error)));
    struct stat info;
    REQUIRE(lstat(path, &info) != 0 && errno == ENOENT);
    (void)digest_b;
    gbb_destroy(machine);
    free(path);
    cart_case_free(&cart);
    remove_tree(root);
    return 0;
}

/* ---- classification drift (D-23) and the 8 MiB cap ---- */

static int session_classification_drift(const char *rom_path) {
    unsigned battery_cases = 0u, timer_cases = 0u, loaded_cases = 0u;
    for (unsigned type = 0u; type < 256u; ++type) {
        for (unsigned ram_code = 0u; ram_code <= 5u; ++ram_code) {
            uint8_t rom[TEST_ROM_SIZE];
            memset(rom, 0, sizeof(rom));
            rom[0x147u] = (uint8_t)type;
            rom[0x148u] = 0x00u;
            rom[0x149u] = (uint8_t)ram_code;
            fix_test_rom_checksum(rom);
            gbb_instance *core = create_machine();
            gbb_instance *player = create_machine();
            REQUIRE(core != NULL && player != NULL);
            const gbb_error core_result = gbb_load_rom(core, rom, sizeof(rom));
            REQUIRE(write_test_file(rom_path, rom, sizeof(rom)));
            char *owned = NULL;
            player_save_identity identity;
            memset(&identity, 0, sizeof(identity));
            char error[256];
            const bool player_ok = player_session_replace_rom(
                player, &owned, rom_path, &identity, error, sizeof(error));
            if (player_ok != (core_result == GBB_OK)) {
                fprintf(stderr, "classification drift: type %02x ram %u load disagreement\n",
                        type, ram_code);
                return 1;
            }
            if (player_ok) {
                ++loaded_cases;
                size_t image = 0u;
                const gbb_error size_result = gbb_battery_size(core, &image);
                const gbb_error rtc_result = gbb_rtc_catch_up(core, 0);
                const bool backed = size_result == GBB_OK;
                const bool rtc = rtc_result == GBB_OK;
                const size_t ram = backed ? image - (rtc ? GBB_RTC_BLOCK_SIZE : 0u) : 0u;
                if (identity.battery_backed != backed || identity.rtc_present != rtc ||
                    identity.ram_size != ram ||
                    identity.cartridge_type != (uint8_t)type) {
                    fprintf(stderr, "classification drift: type %02x ram %u\n", type, ram_code);
                    return 1;
                }
                if (backed) ++battery_cases;
                if (rtc) ++timer_cases;
            }
            free(owned);
            gbb_destroy(core);
            gbb_destroy(player);
        }
    }
    REQUIRE(loaded_cases > 0u && battery_cases > 0u && timer_cases > 0u);
    (void)unlink(rom_path);
    return 0;
}

static int session_rom_cap_8mib(const char *rom_path) {
    const size_t cap = (size_t)8u * 1024u * 1024u;
    size_t size = 0u;
    uint8_t *rom = build_cart_rom(0x19u, 0x08u, 0x00u, 0x77u, &size);
    REQUIRE(rom != NULL && size == cap);
    REQUIRE(write_test_file(rom_path, rom, size));
    gbb_instance *machine = create_machine();
    REQUIRE(machine != NULL);
    char *owned = NULL;
    player_save_identity identity = {0};
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &owned, rom_path, &identity,
                                       error, sizeof(error)));
    REQUIRE(!identity.battery_backed);
    uint8_t *longer = malloc(cap + 1u);
    REQUIRE(longer != NULL);
    memcpy(longer, rom, cap);
    longer[cap] = 0u;
    /* The core's own bound agrees: one byte past 8 MiB is too large. */
    gbb_instance *core = create_machine();
    REQUIRE(core != NULL);
    REQUIRE(gbb_load_rom(core, longer, cap + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(write_test_file(rom_path, longer, cap + 1u));
    char *before = owned;
    REQUIRE(!player_session_replace_rom(machine, &owned, rom_path, &identity,
                                        error, sizeof(error)));
    REQUIRE(owned == before && strstr(error, "8 MiB read bound") != NULL);
    free(owned);
    gbb_destroy(core);
    gbb_destroy(machine);
    free(longer);
    free(rom);
    (void)unlink(rom_path);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 5 || !start_test_root(argv[4])) return 2;
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
    else if (strcmp(argv[1], "player_session_v2_max_size") == 0)
        result = session_v2_max_size(argv[4]);
    else if (strcmp(argv[1], "player_session_v2_reject_matrix") == 0)
        result = session_v2_reject_matrix(argv[4]);
    else if (strcmp(argv[1], "player_session_v2_temp_create_failure") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_FAULT_TEMP_CREATE, false, 0x10u);
    else if (strcmp(argv[1], "player_session_v2_short_write_failure") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_FAULT_SHORT_WRITE, false, 0x10u);
    else if (strcmp(argv[1], "player_session_v2_file_sync_failure") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_FAULT_FILE_SYNC, false, 0x10u);
    else if (strcmp(argv[1], "player_session_v2_rename_failure") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_FAULT_RENAME, false, 0x1Bu);
    else if (strcmp(argv[1], "player_session_v2_directory_sync_failure") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_FAULT_DIRECTORY_SYNC, true, 0x10u);
    else if (strcmp(argv[1], "player_session_v2_interrupt_before_rename") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME, false, 0x10u);
    else if (strcmp(argv[1], "player_session_v2_interrupt_after_rename") == 0)
        result = session_v2_fault(argv[4], PLAYER_SESSION_TEST_INTERRUPT_AFTER_RENAME, true, 0x10u);
    else if (strcmp(argv[1], "player_session_v1_corpus_load") == 0)
        result = argc == 6 ? session_v1_corpus_load(argv[4], argv[3], argv[5]) : 2;
    else if (strcmp(argv[1], "player_session_v1_mbc1_write_identical") == 0)
        result = argc == 6 ? session_v1_mbc1_write_identical(argv[4], argv[3], argv[5]) : 2;
    else if (strcmp(argv[1], "player_session_v1_v2_stickiness") == 0)
        result = session_v1_v2_stickiness(argv[4]);
    else if (strcmp(argv[1], "player_session_classification_drift") == 0)
        result = session_classification_drift(argv[3]);
    else if (strcmp(argv[1], "player_session_rom_cap_8mib") == 0)
        result = session_rom_cap_8mib(argv[3]);
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
    else if (strcmp(argv[1], "player_session_script_no_input") == 0)
        result = argc == 7 ? script_no_input(argv[5], argv[6]) : 2;
    else if (strcmp(argv[1], "player_session_script_invalid") == 0)
        result = argc == 7 ? script_invalid(argv[5], argv[6], argv[2], argv[4]) : 2;
    remove_tree(argv[4]);
    return result;
}
