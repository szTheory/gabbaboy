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
#define SAVE_V1_HEADER_SIZE 51u
#define SAVE_V2_HEADER_SIZE 64u
#define SAVE_MAX_SIZE 131200u
#define RTC_BLOCK_SIZE 21u
#define CHILD_TIMEOUT_NS UINT64_C(5000000000)
#define BASE_CLOCK INT64_C(1700000000)
#define RESULT_FILE "gbb-child-result.txt"

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

/* What the fixture's header promises, computed here without the adapter:
 * the file name rule, the envelope header size and the payload sizes. */
typedef struct {
    uint8_t type;
    uint32_t ram_size;   /* cartridge RAM bytes, excluding any clock block */
    uint32_t rtc_size;   /* 21 for timer cartridges, otherwise 0 */
    uint32_t header;     /* 51 for the v0.1 MBC1 file, otherwise 64 */
    size_t file_size;
} fixture_shape;

static fixture_shape shape_of(const uint8_t *rom) {
    fixture_shape shape;
    shape.type = rom[0x147u];
    switch (rom[0x149u]) {
    case 0x02u: shape.ram_size = 8192u; break;
    case 0x03u: shape.ram_size = 32768u; break;
    case 0x04u: shape.ram_size = 131072u; break;
    case 0x05u: shape.ram_size = 65536u; break;
    default: shape.ram_size = 0u; break;
    }
    if (shape.type == 0x05u || shape.type == 0x06u) shape.ram_size = 512u;
    shape.rtc_size = (shape.type == 0x0Fu || shape.type == 0x10u) ?
                     RTC_BLOCK_SIZE : 0u;
    shape.header = shape.type == 0x03u ? SAVE_V1_HEADER_SIZE :
                                         SAVE_V2_HEADER_SIZE;
    shape.file_size = (size_t)shape.header + shape.ram_size + shape.rtc_size;
    return shape;
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
    const fixture_shape shape = shape_of(rom);
    char basename[112];
    const int name_length = snprintf(basename, sizeof(basename),
        "%s-%s-%02x-%08x.gbb", digest_hex,
        shape.type == 0x03u ? "mbc1" : "cart", (unsigned)shape.type,
        (unsigned)shape.ram_size);
    return name_length >= 0 && (size_t)name_length < sizeof(basename) &&
           path_join(out_path, capacity, pref_path, basename);
}

static uint32_t read_u32_le(const uint8_t bytes[4]) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static int64_t read_i64_le(const uint8_t bytes[8]) {
    uint64_t value = 0u;
    for (unsigned i = 0u; i < 8u; ++i) value |= (uint64_t)bytes[i] << (i * 8u);
    return (int64_t)value;
}

/* Header checks that do not borrow the adapter's decoder. expected_saved_at is
 * ignored unless has_stamp. v2 flags: bit 0 clock block, bit 1 saved_at. */
static bool valid_envelope(const uint8_t *bytes, size_t size,
                           const uint8_t digest[32], const fixture_shape *shape,
                           bool has_stamp, int64_t expected_saved_at) {
    if (size != shape->file_size || memcmp(bytes, "GBBBSAVE", 8u) != 0 ||
        memcmp(bytes + 10u, digest, 32u) != 0 || bytes[42] != shape->type)
        return false;
    if (shape->header == SAVE_V1_HEADER_SIZE)
        return bytes[8] == 1u && bytes[9] == 0u &&
               read_u32_le(bytes + 43u) == shape->ram_size;
    const uint8_t flags = (uint8_t)((shape->rtc_size != 0u ? 1u : 0u) |
                                    (has_stamp ? 2u : 0u));
    return bytes[8] == 2u && bytes[9] == 0u && bytes[43] == flags &&
           read_u32_le(bytes + 44u) == shape->ram_size &&
           read_u32_le(bytes + 48u) == shape->rtc_size &&
           read_i64_le(bytes + 52u) == (has_stamp ? expected_saved_at : 0);
}

static uint64_t monotonic_ns(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0u;
    return (uint64_t)now.tv_sec * UINT64_C(1000000000) +
           (uint64_t)now.tv_nsec;
}

/* Spawns a fresh process. With expect_stop the child must stop itself (the
 * save fault hook raises SIGSTOP before the rename); it is then killed, which
 * models a process dying mid-save. Otherwise it must exit 0 within the bound. */
static bool run_child_ex(const char *executable, const char *mode,
                         const char *rom_path, const char *pref_path,
                         const char *clock, bool expect_stop) {
    char *const arguments[] = {(char *)executable, "--child", (char *)mode,
        (char *)rom_path, (char *)pref_path, (char *)clock, NULL};
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
        const pid_t waited = waitpid(child, &status,
                                     WNOHANG | (expect_stop ? WUNTRACED : 0));
        if (waited == child) {
            if (expect_stop && WIFSTOPPED(status)) {
                (void)kill(child, SIGKILL);
                (void)waitpid(child, NULL, 0);
                return true;
            }
            return !expect_stop && WIFEXITED(status) &&
                   WEXITSTATUS(status) == 0;
        }
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

static bool run_child(const char *executable, const char *mode,
                      const char *rom_path, const char *pref_path,
                      const char *clock) {
    return run_child_ex(executable, mode, rom_path, pref_path, clock, false);
}

static void clock_arg(char out[32], int64_t value) {
    (void)snprintf(out, 32u, "%lld", (long long)value);
}

typedef struct {
    uint8_t wram[7];     /* C000..C006 */
    char status[192];
} child_result;

static bool write_child_result(const char *pref_path, gbb_instance *machine,
                               const char *status) {
    char text[320], path[4096];
    const int length = snprintf(text, sizeof(text),
        "R %02x %02x %02x %02x %02x %02x %02x\nS %s\n",
        (unsigned)gbb_peek_ram(machine, 0xC000u),
        (unsigned)gbb_peek_ram(machine, 0xC001u),
        (unsigned)gbb_peek_ram(machine, 0xC002u),
        (unsigned)gbb_peek_ram(machine, 0xC003u),
        (unsigned)gbb_peek_ram(machine, 0xC004u),
        (unsigned)gbb_peek_ram(machine, 0xC005u),
        (unsigned)gbb_peek_ram(machine, 0xC006u), status);
    return length > 0 && (size_t)length < sizeof(text) &&
           path_join(path, sizeof(path), pref_path, RESULT_FILE) &&
           write_regular_file(path, (const uint8_t *)text, (size_t)length);
}

static bool read_child_result(const char *pref_path, child_result *out) {
    char path[4096];
    uint8_t text[400];
    size_t size = 0u;
    if (!path_join(path, sizeof(path), pref_path, RESULT_FILE) ||
        !read_regular_file(path, text, sizeof(text) - 1u, &size)) return false;
    text[size] = '\0';
    unsigned v[7];
    if (sscanf((const char *)text, "R %x %x %x %x %x %x %x", &v[0], &v[1],
               &v[2], &v[3], &v[4], &v[5], &v[6]) != 7) return false;
    for (unsigned i = 0u; i < 7u; ++i) out->wram[i] = (uint8_t)v[i];
    /* The status line is "S " plus text that may be empty, so it is located
     * by hand: a scanf space would also swallow the newline. */
    const char *status = strstr((const char *)text, "\nS ");
    if (status == NULL) return false;
    status += 3;
    const char *end = strchr(status, '\n');
    if (end == NULL || (size_t)(end - status) >= sizeof(out->status))
        return false;
    memcpy(out->status, status, (size_t)(end - status));
    out->status[end - status] = '\0';
    return true;
}

static bool parse_clock(const char *text, bool *valid, int64_t *value) {
    *valid = strcmp(text, "none") != 0;
    *value = 0;
    if (!*valid) return true;
    char *end = NULL;
    errno = 0;
    const long long parsed = strtoll(text, &end, 10);
    if (text[0] == '\0' || end == NULL || *end != '\0' || errno != 0)
        return false;
    *value = (int64_t)parsed;
    return true;
}

static int run_guest_child(const char *mode, const char *rom_path,
                           const char *pref_path, const char *clock_text) {
    player_session_test_set_pref_path(pref_path);
    gbb_instance *machine = NULL;
    char *owned_path = NULL;
    player_save_identity identity = {0};
    int lock_fd = -1;
    char error[192];
    char status[192] = "";
    int result = 10;
    bool clock_valid = false;
    int64_t clock_now = 0;
    if (!parse_clock(clock_text, &clock_valid, &clock_now)) return 9;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) goto done;
    if (!player_session_replace_rom(machine, &owned_path, rom_path, &identity,
                                    error, sizeof(error))) goto done;
    const bool mbc1 = identity.cartridge_type == 0x03u;
    if (!identity.battery_backed ||
        (mbc1 && identity.ram_size != CONTINUATION_RAM_SIZE)) goto done;
    if (player_session_lock_battery(&identity, &lock_fd,
            error, sizeof(error)) != PLAYER_SESSION_LOCK_ACQUIRED) {
        result = 11;
        goto done;
    }
    player_session_set_clock(&identity, clock_now, clock_valid);
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
    if (strcmp(mode, "seed") == 0) {
        /* Plants the halted-clock mode byte at SRAM $A010 and saves, so the
         * next store run starts the guest in its halted branch. */
        const size_t image_size = (size_t)identity.ram_size + identity.rtc_present *
                                  (size_t)RTC_BLOCK_SIZE;
        uint8_t *image = malloc(image_size);
        const bool seeded = image != NULL && identity.rtc_present &&
            gbb_copy_battery(machine, image, image_size) == GBB_OK &&
            (image[0x10u] = 0x01u, gbb_import_battery(machine, image,
                                                        image_size) == GBB_OK) &&
            player_session_save_battery(machine, &identity, error, sizeof(error));
        free(image);
        result = seeded ? 0 : 21;
        goto done;
    }
    /* D-22: once per open, after the import and before the first instruction. */
    if (!player_session_apply_catch_up(machine, &identity, status,
                                       sizeof(status))) {
        result = 19;
        goto done;
    }
    if (strcmp(mode, "interrupt") == 0) {
        uint64_t generation = 0u;
        if (gbb_battery_generation(machine, &generation) != GBB_OK ||
            generation == identity.saved_generation) {
            result = 22;
            goto done;
        }
        player_session_test_set_fault(PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME);
        (void)player_session_save_battery(machine, &identity, error,
                                          sizeof(error));
        result = 23; /* the fault hook stops the process before this line */
        goto done;
    }
    const gbb_run_result run = gbb_run(machine, 200000u, NULL, 0u);
    /* The MBC1 guest spins on its budget; the newer guests park in HALT. */
    if ((run.reason != GBB_STOP_BUDGET && run.reason != GBB_STOP_HALTED_IDLE) ||
        run.consumed_half_dots == 0u) {
        result = 14;
        goto done;
    }
    if (!write_child_result(pref_path, machine, status)) {
        result = 24;
        goto done;
    }

    if (strcmp(mode, "store") == 0) {
        uint64_t generation = 0u;
        const bool fresh_marks = mbc1 ?
            gbb_peek_ram(machine, 0xC000u) == 1u &&
            gbb_peek_ram(machine, 0xC001u) == 0u &&
            gbb_peek_ram(machine, 0xC002u) == 0xE1u :
            gbb_peek_ram(machine, 0xC000u) == 1u;
        if (!fresh_marks ||
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
        if (mbc1)
            result = gbb_peek_ram(machine, 0xC001u) == 0xA5u &&
                     gbb_peek_ram(machine, 0xC004u) == 1u ? 0 : 17;
        else if (identity.rtc_present)
            result = gbb_peek_ram(machine, 0xC000u) == 2u &&
                     gbb_peek_ram(machine, 0xC006u) == 0xA5u ? 0 : 17;
        else
            result = gbb_peek_ram(machine, 0xC000u) == 2u &&
                     gbb_peek_ram(machine, 0xC001u) == 0xA5u ? 0 : 17;
    } else {
        /* "empty", "wrong" and "mutated": no save was accepted, so the guest
         * took its fresh-RAM branch and no resume marker exists. */
        if (mbc1)
            result = gbb_peek_ram(machine, 0xC001u) == 0u &&
                     gbb_peek_ram(machine, 0xC000u) == 1u &&
                     gbb_peek_ram(machine, 0xC002u) == 0xE1u ? 0 : 18;
        else
            result = gbb_peek_ram(machine, 0xC000u) == 1u &&
                     gbb_peek_ram(machine, 0xC001u) != 0xA5u &&
                     gbb_peek_ram(machine, 0xC006u) != 0xA5u ? 0 : 18;
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

/* Runs a store child at the given clock and returns the envelope it wrote,
 * after the independent header check. */
static bool get_saved_envelope(const char *executable, const char *rom_path,
                               const char *pref_path, const char *clock,
                               const uint8_t rom[CONTINUATION_ROM_SIZE],
                               char save_path[4096], uint8_t digest[32],
                               uint8_t bytes[SAVE_MAX_SIZE], size_t *out_size) {
    const fixture_shape shape = shape_of(rom);
    bool valid = false;
    int64_t value = 0;
    return parse_clock(clock, &valid, &value) &&
        run_child(executable, "store", rom_path, pref_path, clock) &&
        expected_save_path(pref_path, rom, CONTINUATION_ROM_SIZE, save_path,
                           4096u, digest) &&
        read_regular_file(save_path, bytes, SAVE_MAX_SIZE, out_size) &&
        valid_envelope(bytes, *out_size, digest, &shape,
                       valid && shape.rtc_size != 0u, value);
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
        uint8_t actual[SAVE_MAX_SIZE];
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

/* ---- MBC1 scenarios (unchanged protocol; the clock is irrelevant) ---- */

static bool continuation_resume(const char *executable, const char *rom_path,
                                const uint8_t rom[CONTINUATION_ROM_SIZE],
                                const char *root) {
    char pref_path[4096], save_path[4096];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE];
    size_t size = 0u;
    if (!make_pref_directory(root, "positive", pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, "none", rom,
                            save_path, digest, envelope, &size) ||
        !run_child(executable, "resume", rom_path, pref_path, "none"))
        return false;
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
        !run_child(executable, "empty", rom_path, pref_path, "none") ||
        lstat(save_path, &info) == 0 || errno != ENOENT) return false;
    puts("MISSING_SAVE_EMPTY");
    return true;
}

/* Writes the title-byte variant of the fixture (same type and sizes, fixed
 * header checksum, different digest) to root/name. */
static bool make_variant(const uint8_t rom[CONTINUATION_ROM_SIZE],
                         const char *root, const char *name,
                         uint8_t variant[CONTINUATION_ROM_SIZE],
                         char out_path[4096]) {
    memcpy(variant, rom, CONTINUATION_ROM_SIZE);
    variant[0x134u] = variant[0x134u] == (uint8_t)'V' ? (uint8_t)'W' :
                                                         (uint8_t)'V';
    fix_header_checksum(variant);
    return path_join(out_path, 4096u, root, name) &&
           write_regular_file(out_path, variant, CONTINUATION_ROM_SIZE);
}

static bool continuation_wrong_rom(const char *executable, const char *rom_path,
                                   const uint8_t rom[CONTINUATION_ROM_SIZE],
                                   const char *root) {
    char original_pref[4096], wrong_pref[4096], original_path[4096];
    char variant_path[4096], variant_save_path[4096];
    uint8_t original_digest[32], variant_digest[32];
    uint8_t envelope[SAVE_MAX_SIZE], variant[CONTINUATION_ROM_SIZE];
    size_t size = 0u;
    if (!make_pref_directory(root, "wrong-original", original_pref) ||
        !make_pref_directory(root, "wrong-variant", wrong_pref) ||
        !get_saved_envelope(executable, rom_path, original_pref, "none", rom,
                            original_path, original_digest, envelope, &size))
        return false;
    if (!make_variant(rom, root, "wrong-rom.gb", variant, variant_path) ||
        !expected_save_path(wrong_pref, variant, sizeof(variant),
                            variant_save_path, sizeof(variant_save_path),
                            variant_digest) ||
        memcmp(original_digest, variant_digest, sizeof(original_digest)) == 0 ||
        !write_regular_file(variant_save_path, envelope, size) ||
        !run_child(executable, "wrong", variant_path, wrong_pref, "none") ||
        !recovery_matches(wrong_pref, variant_save_path, envelope, size))
        return false;
    puts("WRONG_ROM_IDENTITY_REJECTED");
    return true;
}

static bool continuation_mutated_payload(const char *executable,
                                         const char *rom_path,
                                         const uint8_t rom[CONTINUATION_ROM_SIZE],
                                         const char *root) {
    char pref_path[4096], save_path[4096];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE];
    size_t size = 0u;
    if (!make_pref_directory(root, "mutated", pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, "none", rom,
                            save_path, digest, envelope, &size)) return false;
    envelope[SAVE_V1_HEADER_SIZE + 1u] ^= 0x01u; /* leave the checksum stale */
    if (!write_regular_file(save_path, envelope, size) ||
        !run_child(executable, "mutated", rom_path, pref_path, "none") ||
        !recovery_matches(pref_path, save_path, envelope, size))
        return false;
    puts("ALTERED_PAYLOAD_REJECTED");
    return true;
}

/* ---- MBC3 + RTC scenarios ---- */

/* Seconds since the guest's 00:00:00 day 0, counting the 512-day carry. The
 * emulated seconds the guest ran before latching are common to every run and
 * cancel when two totals are subtracted (the manifest's host_delta_rule). */
static int64_t clock_total(const child_result *result) {
    const int64_t seconds = result->wram[1], minutes = result->wram[2];
    const int64_t hours = result->wram[3];
    const int64_t days = (int64_t)result->wram[4] |
                         (int64_t)(result->wram[5] & 1u) << 8;
    const int64_t carry = (result->wram[5] >> 7) & 1u;
    return (((carry * 512 + days) * 24 + hours) * 60 + minutes) * 60 + seconds;
}

/* Stores at BASE_CLOCK in pref, then resumes at BASE_CLOCK + offset (or the
 * clock text) and reads the result file. */
static bool resume_with(const char *executable, const char *rom_path,
                        const char *pref_path, const char *clock,
                        child_result *out) {
    return run_child(executable, "resume", rom_path, pref_path, clock) &&
           read_child_result(pref_path, out) && out->wram[0] == 2u &&
           out->wram[6] == 0xA5u;
}

static bool store_base(const char *executable, const char *rom_path,
                       const uint8_t rom[CONTINUATION_ROM_SIZE],
                       const char *pref_path, char save_path[4096],
                       uint8_t digest[32], uint8_t envelope[SAVE_MAX_SIZE],
                       size_t *size) {
    char clock[32];
    clock_arg(clock, BASE_CLOCK);
    return get_saved_envelope(executable, rom_path, pref_path, clock, rom,
                              save_path, digest, envelope, size);
}

/* The same-process baseline: resume at the stamped time, no catch-up, status
 * empty. Returns total(0) for later subtraction. */
static bool baseline_total(const char *executable, const char *rom_path,
                           const char *pref_path, int64_t *out_total) {
    char clock[32];
    child_result result;
    clock_arg(clock, BASE_CLOCK);
    if (!resume_with(executable, rom_path, pref_path, clock, &result) ||
        result.status[0] != '\0') return false;
    *out_total = clock_total(&result);
    return true;
}

static bool rtc_resume(const char *executable, const char *rom_path,
                       const uint8_t rom[CONTINUATION_ROM_SIZE],
                       const char *root) {
    char pref_path[4096], save_path[4096], clock[32];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE], after[SAVE_MAX_SIZE];
    size_t size = 0u, after_size = 0u;
    int64_t baseline = 0;
    child_result result;
    if (!make_pref_directory(root, "rtc-resume", pref_path) ||
        !store_base(executable, rom_path, rom, pref_path, save_path, digest,
                    envelope, &size) ||
        !baseline_total(executable, rom_path, pref_path, &baseline)) return false;
    /* RTC-03 concurrency edge: a process killed while saving leaves the last
     * good file, byte for byte, and the next process still resumes from it. */
    clock_arg(clock, BASE_CLOCK + 10);
    if (!run_child_ex(executable, "interrupt", rom_path, pref_path, clock, true) ||
        !read_regular_file(save_path, after, sizeof(after), &after_size) ||
        after_size != size || memcmp(after, envelope, size) != 0) return false;
    clock_arg(clock, BASE_CLOCK + 3661);
    if (!resume_with(executable, rom_path, pref_path, clock, &result) ||
        strcmp(result.status, "Game clock advanced by 0d 1h 1m 1s") != 0 ||
        clock_total(&result) - baseline != 3661) return false;
    puts("RTC_RESUMED_EXACT_DELTA");
    return true;
}

static bool rtc_delta(const char *executable, const char *rom_path,
                      const uint8_t rom[CONTINUATION_ROM_SIZE],
                      const char *root) {
    static const int64_t deltas[] = {0, 1, 59, 3600, 86400, 44236860};
    int64_t baseline = 0;
    for (size_t i = 0u; i < sizeof(deltas) / sizeof(deltas[0]); ++i) {
        char name[32], pref_path[4096], save_path[4096], clock[32];
        char expected[96];
        uint8_t digest[32], envelope[SAVE_MAX_SIZE];
        size_t size = 0u;
        child_result result;
        (void)snprintf(name, sizeof(name), "rtc-delta-%zu", i);
        if (!make_pref_directory(root, name, pref_path) ||
            !store_base(executable, rom_path, rom, pref_path, save_path,
                        digest, envelope, &size)) return false;
        clock_arg(clock, BASE_CLOCK + deltas[i]);
        if (!resume_with(executable, rom_path, pref_path, clock, &result))
            return false;
        const int64_t total = clock_total(&result);
        if (i == 0u) baseline = total;
        if (total - baseline != deltas[i]) return false;
        const int64_t d = deltas[i];
        if (d == 0) expected[0] = '\0';
        else (void)snprintf(expected, sizeof(expected),
            "Game clock advanced by %lldd %lldh %lldm %llds%s",
            (long long)(d / 86400), (long long)(d % 86400 / 3600),
            (long long)(d % 3600 / 60), (long long)(d % 60),
            d == 44236860 ? " (day counter overflowed)" : "");
        if (strcmp(result.status, expected) != 0) return false;
        /* 44236860 = 512 days + 60 s: the carry must be set, nothing else. */
        if ((d == 44236860) != ((result.wram[5] & 0x80u) != 0u)) return false;
    }
    puts("RTC_DELTAS_EXACT");
    return true;
}

static bool rtc_rollback(const char *executable, const char *rom_path,
                         const uint8_t rom[CONTINUATION_ROM_SIZE],
                         const char *root) {
    char pref_path[4096], save_path[4096], clock[32];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE], after[SAVE_MAX_SIZE];
    size_t size = 0u, after_size = 0u;
    int64_t baseline = 0;
    child_result result;
    if (!make_pref_directory(root, "rtc-rollback", pref_path) ||
        !store_base(executable, rom_path, rom, pref_path, save_path, digest,
                    envelope, &size) ||
        !baseline_total(executable, rom_path, pref_path, &baseline)) return false;
    clock_arg(clock, BASE_CLOCK - 100);
    if (!resume_with(executable, rom_path, pref_path, clock, &result) ||
        strcmp(result.status, "Game clock not advanced: the system clock is earlier than the save.") != 0 ||
        clock_total(&result) != baseline ||
        !read_regular_file(save_path, after, sizeof(after), &after_size) ||
        after_size != size || memcmp(after, envelope, size) != 0) return false;
    puts("RTC_ROLLBACK_NOT_APPLIED");
    return true;
}

static bool rtc_halted(const char *executable, const char *rom_path,
                       const uint8_t rom[CONTINUATION_ROM_SIZE],
                       const char *root) {
    char pref_path[4096], save_path[4096], clock[32];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE];
    size_t size = 0u;
    child_result result;
    clock_arg(clock, BASE_CLOCK);
    if (!make_pref_directory(root, "rtc-halted", pref_path) ||
        !run_child(executable, "seed", rom_path, pref_path, clock) ||
        !get_saved_envelope(executable, rom_path, pref_path, clock, rom,
                            save_path, digest, envelope, &size)) return false;
    clock_arg(clock, BASE_CLOCK + 86400);
    /* 12:34:56 day 0 with DH = $40 (halt set): the delta is ignored. */
    if (!resume_with(executable, rom_path, pref_path, clock, &result) ||
        strcmp(result.status, "Game clock is halted; not advanced.") != 0 ||
        result.wram[1] != 56u || result.wram[2] != 34u ||
        result.wram[3] != 12u || result.wram[4] != 0u ||
        result.wram[5] != 0x40u) return false;
    puts("RTC_HALTED_NOT_ADVANCED");
    return true;
}

static bool rtc_no_clock(const char *executable, const char *rom_path,
                         const uint8_t rom[CONTINUATION_ROM_SIZE],
                         const char *root) {
    char pref_path[4096], save_path[4096], clock[32];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE];
    size_t size = 0u;
    int64_t baseline = 0;
    child_result result;
    if (!make_pref_directory(root, "rtc-no-clock-a", pref_path) ||
        !store_base(executable, rom_path, rom, pref_path, save_path, digest,
                    envelope, &size) ||
        !baseline_total(executable, rom_path, pref_path, &baseline) ||
        !resume_with(executable, rom_path, pref_path, "none", &result) ||
        strcmp(result.status, "Game clock not advanced: the system clock is unavailable.") != 0 ||
        clock_total(&result) != baseline) return false;
    /* A store with no clock records no time stamp (flags bit 1 clear). */
    if (!make_pref_directory(root, "rtc-no-clock-b", pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, "none", rom,
                            save_path, digest, envelope, &size)) return false;
    clock_arg(clock, BASE_CLOCK);
    if (!resume_with(executable, rom_path, pref_path, clock, &result) ||
        strcmp(result.status, "Game clock not advanced: the save has no time stamp.") != 0 ||
        clock_total(&result) != baseline) return false;
    puts("RTC_NO_CLOCK_NOT_ADVANCED");
    return true;
}

static bool rtc_wrong_rom(const char *executable, const char *rom_path,
                          const uint8_t rom[CONTINUATION_ROM_SIZE],
                          const char *root) {
    char original_pref[4096], wrong_pref[4096], original_path[4096];
    char variant_path[4096], variant_save_path[4096], clock[32];
    uint8_t original_digest[32], variant_digest[32];
    uint8_t envelope[SAVE_MAX_SIZE], variant[CONTINUATION_ROM_SIZE];
    size_t size = 0u;
    int64_t baseline = 0;
    child_result result;
    if (!make_pref_directory(root, "rtc-wrong-original", original_pref) ||
        !make_pref_directory(root, "rtc-wrong-variant", wrong_pref) ||
        !store_base(executable, rom_path, rom, original_pref, original_path,
                    original_digest, envelope, &size) ||
        !baseline_total(executable, rom_path, original_pref, &baseline))
        return false;
    /* The variant has the same type and sizes, so it maps to a file name of
     * the same shape; the original's envelope under that name must be refused
     * (digest mismatch), preserved, and replaced by fresh RAM. */
    if (!make_variant(rom, root, "rtc-wrong-rom.gb", variant, variant_path) ||
        !expected_save_path(wrong_pref, variant, sizeof(variant),
                            variant_save_path, sizeof(variant_save_path),
                            variant_digest) ||
        memcmp(original_digest, variant_digest, sizeof(original_digest)) == 0 ||
        !write_regular_file(variant_save_path, envelope, size)) return false;
    clock_arg(clock, BASE_CLOCK + 100);
    if (!run_child(executable, "wrong", variant_path, wrong_pref, clock) ||
        !read_child_result(wrong_pref, &result) || result.wram[0] != 1u ||
        result.wram[6] == 0xA5u || result.status[0] != '\0' ||
        !recovery_matches(wrong_pref, variant_save_path, envelope, size))
        return false;
    /* The original save was never touched and still resumes. */
    clock_arg(clock, BASE_CLOCK + 3661);
    if (!resume_with(executable, rom_path, original_pref, clock, &result) ||
        clock_total(&result) - baseline != 3661) return false;
    puts("RTC_WRONG_ROM_REJECTED");
    return true;
}

/* ---- MBC2 and MBC5 resume ---- */

static bool plain_resume(const char *executable, const char *rom_path,
                         const uint8_t rom[CONTINUATION_ROM_SIZE],
                         const char *root, const char *name) {
    char pref_path[4096], save_path[4096], clock[32];
    uint8_t digest[32], envelope[SAVE_MAX_SIZE];
    size_t size = 0u;
    child_result result;
    clock_arg(clock, BASE_CLOCK);
    if (!make_pref_directory(root, name, pref_path) ||
        !get_saved_envelope(executable, rom_path, pref_path, clock, rom,
                            save_path, digest, envelope, &size) ||
        !run_child(executable, "resume", rom_path, pref_path, clock) ||
        !read_child_result(pref_path, &result) || result.wram[0] != 2u ||
        result.wram[1] != 0xA5u || result.status[0] != '\0') return false;
    puts("BATTERY_RESUMED");
    return true;
}

static int run_named_test(const char *name, const char *executable,
                          const char *rom_path, const char *root) {
    uint8_t rom[CONTINUATION_ROM_SIZE];
    if (!read_rom(rom_path, rom)) return 1;
    const bool is_rtc = strncmp(name, "player_continuation_mbc3_", 25u) == 0;
    const bool is_mbc2 = strcmp(name, "player_continuation_mbc2_resume") == 0;
    const bool is_mbc5 = strcmp(name, "player_continuation_mbc5_resume") == 0;
    const bool type_ok = is_rtc ? rom[0x147u] == 0x10u && rom[0x149u] == 0x02u :
                         is_mbc2 ? rom[0x147u] == 0x06u :
                         is_mbc5 ? rom[0x147u] == 0x1Bu && rom[0x149u] == 0x04u :
                         rom[0x147u] == 0x03u && rom[0x149u] == 0x02u;
    if (rom[0x148u] != 0x00u || !type_ok) return 1;
    bool passed = false;
    if (strcmp(name, "player_continuation_resume") == 0)
        passed = continuation_resume(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_missing_save") == 0)
        passed = continuation_missing(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_wrong_rom") == 0)
        passed = continuation_wrong_rom(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mutated_payload") == 0)
        passed = continuation_mutated_payload(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_rtc_resume") == 0)
        passed = rtc_resume(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_rtc_delta") == 0)
        passed = rtc_delta(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_rtc_rollback") == 0)
        passed = rtc_rollback(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_rtc_halted") == 0)
        passed = rtc_halted(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_rtc_no_clock") == 0)
        passed = rtc_no_clock(executable, rom_path, rom, root);
    else if (strcmp(name, "player_continuation_mbc3_wrong_rom") == 0)
        passed = rtc_wrong_rom(executable, rom_path, rom, root);
    else if (is_mbc2 || is_mbc5)
        passed = plain_resume(executable, rom_path, rom, root,
                              is_mbc2 ? "mbc2" : "mbc5");
    remove_tree(root);
    if (!passed) fputs("Continuation scenario failed its bounded oracle\n", stderr);
    return passed ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc == 6 && strcmp(argv[1], "--child") == 0)
        return run_guest_child(argv[2], argv[3], argv[4], argv[5]);
    if (argc != 4) return 2;
    remove_tree(argv[3]);
    if (mkdir(argv[3], 0700) != 0) return 2;
    return run_named_test(argv[1], argv[0], argv[2], argv[3]);
}
