#include "session.h"

#include <CommonCrypto/CommonDigest.h>

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define CONTINUATION_ROM_SIZE 32768u
#define CONTINUATION_RAM_SIZE 8192u
#define SAVE_HEADER_SIZE 51u
#define SAVE_FILE_SIZE (SAVE_HEADER_SIZE + CONTINUATION_RAM_SIZE)
#define CHILD_TIMEOUT_NS UINT64_C(5000000000)

extern char **environ;

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
            const int length = snprintf(child, sizeof(child), "%s/%s",
                                        path, entry->d_name);
            if (length >= 0 && (size_t)length < sizeof(child))
                remove_tree(child);
        }
        (void)closedir(directory);
    }
    (void)rmdir(path);
}

static bool path_join(char *out, size_t capacity, const char *left,
                      const char *right) {
    const int length = snprintf(out, capacity, "%s/%s", left, right);
    return length >= 0 && (size_t)length < capacity;
}

static bool read_regular_file(const char *path, uint8_t *bytes,
                              size_t capacity, size_t *out_size) {
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
        if (count > 0) total += (size_t)count;
        else if (count < 0 && errno == EINTR) continue;
        else {
            (void)close(fd);
            return false;
        }
    }
    if (close(fd) != 0) return false;
    *out_size = total;
    return true;
}

static bool write_regular_file(const char *path, const uint8_t *bytes,
                               size_t size) {
    const int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC |
                        O_NOFOLLOW, S_IRUSR | S_IWUSR);
    if (fd < 0) return false;
    size_t total = 0u;
    while (total < size) {
        const ssize_t count = write(fd, bytes + total, size - total);
        if (count > 0) total += (size_t)count;
        else if (count < 0 && errno == EINTR) continue;
        else {
            (void)close(fd);
            return false;
        }
    }
    return close(fd) == 0;
}

static bool read_rom(const char *path, uint8_t rom[CONTINUATION_ROM_SIZE]) {
    size_t size = 0u;
    return read_regular_file(path, rom, CONTINUATION_ROM_SIZE, &size) &&
           size == CONTINUATION_ROM_SIZE;
}

static bool identify_digest(const uint8_t *rom, size_t size,
                            uint8_t out_digest[32]) {
    return rom != NULL && size <= UINT32_MAX &&
           CC_SHA256(rom, (CC_LONG)size, out_digest) != NULL;
}

/* This path calculation is intentionally independent of the adapter's test
 * path helper; it pins the documented digest/type/RAM filename contract. */
static bool expected_save_path(const char *pref_path, const uint8_t *rom,
                               size_t rom_size, char *out_path,
                               size_t capacity, uint8_t out_digest[32]) {
    if (!identify_digest(rom, rom_size, out_digest)) return false;
    static const char hex[] = "0123456789abcdef";
    char digest_hex[65];
    for (size_t i = 0u; i < 32u; ++i) {
        digest_hex[i * 2u] = hex[out_digest[i] >> 4];
        digest_hex[i * 2u + 1u] = hex[out_digest[i] & 0x0Fu];
    }
    digest_hex[64] = '\0';
    const uint8_t type = rom[0x147u];
    const uint32_t ram_size = rom[0x149u] == 0x02u ? 8192u :
                              rom[0x149u] == 0x03u ? 32768u : 0u;
    char basename[112];
    const int name_length = snprintf(basename, sizeof(basename),
        "%s-mbc1-%02x-%08x.gbb", digest_hex, (unsigned)type,
        (unsigned)ram_size);
    return name_length >= 0 && (size_t)name_length < sizeof(basename) &&
           path_join(out_path, capacity, pref_path, basename);
}

static uint32_t read_u32_le(const uint8_t bytes[4]) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static bool valid_original_envelope(const uint8_t *bytes, size_t size,
                                    const uint8_t digest[32]) {
    return size == SAVE_FILE_SIZE && memcmp(bytes, "GBBBSAVE", 8u) == 0 &&
        bytes[8] == 1u && bytes[9] == 0u &&
        memcmp(bytes + 10u, digest, 32u) == 0 && bytes[42] == 0x03u &&
        read_u32_le(bytes + 43u) == CONTINUATION_RAM_SIZE;
}

static uint64_t monotonic_ns(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0u;
    return (uint64_t)now.tv_sec * UINT64_C(1000000000) +
           (uint64_t)now.tv_nsec;
}

static bool run_child(const char *executable, const char *mode,
                      const char *rom_path, const char *pref_path) {
    char *const arguments[] = {(char *)executable, "--child", (char *)mode,
        (char *)rom_path, (char *)pref_path, NULL};
    pid_t child = 0;
    if (posix_spawnp(&child, executable, NULL, NULL, arguments, environ) != 0)
        return false;
    const uint64_t started = monotonic_ns();
    if (started == 0u) {
        (void)kill(child, SIGKILL);
        (void)waitpid(child, NULL, 0);
        return false;
    }
    for (;;) {
        int status = 0;
        const pid_t waited = waitpid(child, &status, WNOHANG);
        if (waited == child)
            return WIFEXITED(status) && WEXITSTATUS(status) == 0;
        if (waited < 0 && errno != EINTR) return false;
        const uint64_t now = monotonic_ns();
        if (now < started || now - started >= CHILD_TIMEOUT_NS) {
            (void)kill(child, SIGKILL);
            (void)waitpid(child, NULL, 0);
            return false;
        }
        const struct timespec pause = {0, 10000000L};
        (void)nanosleep(&pause, NULL);
    }
}

static int run_guest_child(const char *mode, const char *rom_path,
                           const char *pref_path) {
    player_session_test_set_pref_path(pref_path);
    gbb_instance *machine = NULL;
    char *owned_path = NULL;
    player_save_identity identity = {0};
    int lock_fd = -1;
    char error[192];
    int result = 10;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) goto done;
    if (!player_session_replace_rom(machine, &owned_path, rom_path, &identity,
                                    error, sizeof(error))) goto done;
    if (!identity.battery_backed || identity.ram_size != CONTINUATION_RAM_SIZE)
        goto done;
    if (player_session_lock_battery(&identity, &lock_fd,
            error, sizeof(error)) != PLAYER_SESSION_LOCK_ACQUIRED) {
        result = 11;
        goto done;
    }
    const bool load_ok = player_session_load_battery(machine, &identity,
                                                      error, sizeof(error));
    const bool expects_rejection = strcmp(mode, "wrong") == 0 ||
                                   strcmp(mode, "mutated") == 0;
    if (expects_rejection) {
        if (load_ok || !identity.persistence_enabled ||
            strstr(error, "rejected and preserved") == NULL) {
            result = 12;
            goto done;
        }
    } else if (!load_ok || error[0] != '\0') {
        result = 13;
        goto done;
    }
    const gbb_run_result run = gbb_run(machine, 200000u, NULL, 0u);
    if (run.reason != GBB_STOP_BUDGET || run.consumed_half_dots == 0u) {
        result = 14;
        goto done;
    }

    if (strcmp(mode, "store") == 0) {
        uint64_t generation = 0u;
        if (gbb_peek_ram(machine, 0xC000u) != 1u ||
            gbb_peek_ram(machine, 0xC001u) != 0u ||
            gbb_peek_ram(machine, 0xC002u) != 0xE1u ||
            gbb_battery_generation(machine, &generation) != GBB_OK ||
            generation == identity.saved_generation) {
            result = 15;
            goto done;
        }
        if (!player_session_save_battery(machine, &identity,
                                         error, sizeof(error))) {
            result = 16;
            goto done;
        }
        result = 0;
    } else if (strcmp(mode, "resume") == 0) {
        result = gbb_peek_ram(machine, 0xC001u) == 0xA5u &&
                 gbb_peek_ram(machine, 0xC004u) == 1u ? 0 : 17;
    } else {
        result = gbb_peek_ram(machine, 0xC001u) == 0u &&
                 gbb_peek_ram(machine, 0xC000u) == 1u &&
                 gbb_peek_ram(machine, 0xC002u) == 0xE1u ? 0 : 18;
    }

done:
    if (machine != NULL) gbb_destroy(machine);
    player_session_unlock_battery(&lock_fd);
    free(owned_path);
    return result;
}

static bool make_pref_directory(const char *root, const char *name,
                                char out_path[4096]) {
    return path_join(out_path, 4096u, root, name) &&
           mkdir(out_path, 0700) == 0;
}

static bool get_saved_envelope(const char *executable, const char *rom_path,
                               const char *pref_path,
                               const uint8_t rom[CONTINUATION_ROM_SIZE],
                               char save_path[4096], uint8_t digest[32],
                               uint8_t bytes[SAVE_FILE_SIZE]) {
    size_t size = 0u;
    return run_child(executable, "store", rom_path, pref_path) &&
        expected_save_path(pref_path, rom, CONTINUATION_ROM_SIZE, save_path,
                           4096u, digest) &&
        read_regular_file(save_path, bytes, SAVE_FILE_SIZE, &size) &&
        valid_original_envelope(bytes, size, digest);
}

static bool recovery_matches(const char *pref_path, const char *save_path,
                             const uint8_t *expected, size_t expected_size) {
    struct stat info;
    if (lstat(save_path, &info) == 0 || errno != ENOENT) return false;
    const char *basename = strrchr(save_path, '/');
    basename = basename == NULL ? save_path : basename + 1;
    DIR *directory = opendir(pref_path);
    if (directory == NULL) return false;
    bool found = false;
    struct dirent *entry;
    while ((entry = readdir(directory)) != NULL) {
        const size_t base_length = strlen(basename);
        if (strncmp(entry->d_name, basename, base_length) != 0 ||
            strncmp(entry->d_name + base_length, ".recovery-", 10u) != 0)
            continue;
        char recovery_path[4096];
        uint8_t actual[SAVE_FILE_SIZE];
        size_t actual_size = 0u;
        if (!path_join(recovery_path, sizeof(recovery_path), pref_path,
                       entry->d_name) ||
            !read_regular_file(recovery_path, actual, sizeof(actual),
                               &actual_size) || actual_size != expected_size ||
            memcmp(actual, expected, expected_size) != 0 || found) {
            (void)closedir(directory);
            return false;
        }
        found = true;
    }
    (void)closedir(directory);
    return found;
}

static void fix_header_checksum(uint8_t rom[CONTINUATION_ROM_SIZE]) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static bool continuation_resume(const char *executable, const char *rom_path,
                                const uint8_t rom[CONTINUATION_ROM_SIZE],
                                const char *root) {
    char pref_path[4096], save_path[4096];
    uint8_t digest[32], envelope[SAVE_FILE_SIZE];
    if (!make_pref_directory(root, "positive", pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, rom,
                            save_path, digest, envelope) ||
        !run_child(executable, "resume", rom_path, pref_path)) return false;
    puts("CONTINUATION_RESUMED");
    return true;
}

static bool continuation_missing(const char *executable, const char *rom_path,
                                 const uint8_t rom[CONTINUATION_ROM_SIZE],
                                 const char *root) {
    char pref_path[4096], save_path[4096];
    uint8_t digest[32];
    if (!make_pref_directory(root, "missing", pref_path) ||
        !expected_save_path(pref_path, rom, CONTINUATION_ROM_SIZE, save_path,
                           sizeof(save_path), digest)) return false;
    struct stat info;
    if (lstat(save_path, &info) == 0 || errno != ENOENT ||
        !run_child(executable, "empty", rom_path, pref_path) ||
        lstat(save_path, &info) == 0 || errno != ENOENT) return false;
    puts("MISSING_SAVE_EMPTY");
    return true;
}

static bool continuation_wrong_rom(const char *executable, const char *rom_path,
                                   const uint8_t rom[CONTINUATION_ROM_SIZE],
                                   const char *root) {
    char original_pref[4096], wrong_pref[4096], original_path[4096];
    char variant_path[4096], variant_save_path[4096];
    uint8_t original_digest[32], variant_digest[32];
    uint8_t envelope[SAVE_FILE_SIZE], variant[CONTINUATION_ROM_SIZE];
    if (!make_pref_directory(root, "wrong-original", original_pref) ||
        !make_pref_directory(root, "wrong-variant", wrong_pref) ||
        !get_saved_envelope(executable, rom_path, original_pref, rom,
                            original_path, original_digest, envelope)) return false;
    memcpy(variant, rom, sizeof(variant));
    variant[0x134u] = variant[0x134u] == (uint8_t)'V' ? (uint8_t)'W' :
                                                                      (uint8_t)'V';
    fix_header_checksum(variant);
    if (!path_join(variant_path, sizeof(variant_path), root, "wrong-rom.gb") ||
        !write_regular_file(variant_path, variant, sizeof(variant)) ||
        !expected_save_path(wrong_pref, variant, sizeof(variant),
                            variant_save_path, sizeof(variant_save_path),
                            variant_digest) ||
        memcmp(original_digest, variant_digest, sizeof(original_digest)) == 0 ||
        !write_regular_file(variant_save_path, envelope, sizeof(envelope)) ||
        !run_child(executable, "wrong", variant_path, wrong_pref) ||
        !recovery_matches(wrong_pref, variant_save_path, envelope,
                          sizeof(envelope))) return false;
    puts("WRONG_ROM_IDENTITY_REJECTED");
    return true;
}

static bool continuation_mutated_payload(const char *executable,
                                         const char *rom_path,
                                         const uint8_t rom[CONTINUATION_ROM_SIZE],
                                         const char *root) {
    char pref_path[4096], save_path[4096];
    uint8_t digest[32], envelope[SAVE_FILE_SIZE];
    if (!make_pref_directory(root, "mutated", pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, rom,
                            save_path, digest, envelope)) return false;
    envelope[SAVE_HEADER_SIZE + 1u] ^= 0x01u; /* leave the checksum stale */
    if (!write_regular_file(save_path, envelope, sizeof(envelope)) ||
        !run_child(executable, "mutated", rom_path, pref_path) ||
        !recovery_matches(pref_path, save_path, envelope, sizeof(envelope)))
        return false;
    puts("ALTERED_PAYLOAD_REJECTED");
    return true;
}

static int run_named_test(const char *name, const char *executable,
                          const char *rom_path, const char *root) {
    uint8_t rom[CONTINUATION_ROM_SIZE];
    if (!read_rom(rom_path, rom) || rom[0x147u] != 0x03u ||
        rom[0x148u] != 0x00u || rom[0x149u] != 0x02u) return 1;
    bool passed = false;
    if (strcmp(name, "player_continuation_resume") == 0)
        passed = continuation_resume(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_missing_save") == 0)
        passed = continuation_missing(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_wrong_rom") == 0)
        passed = continuation_wrong_rom(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mutated_payload") == 0)
        passed = continuation_mutated_payload(executable, rom_path, rom, root);
    remove_tree(root);
    if (!passed) fputs("MBC1 continuation scenario failed its bounded oracle\n", stderr);
    return passed ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc == 5 && strcmp(argv[1], "--child") == 0)
        return run_guest_child(argv[2], argv[3], argv[4]);
    if (argc != 4) return 2;
    remove_tree(argv[3]);
    if (mkdir(argv[3], 0700) != 0) return 2;
    return run_named_test(argv[1], argv[0], argv[2], argv[3]);
}
