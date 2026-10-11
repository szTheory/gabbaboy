#include "session.h"

#include <CommonCrypto/CommonDigest.h>
#include <SDL3/SDL.h>

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/stdio.h>
#include <unistd.h>
#ifdef GBB_PLAYER_SESSION_TESTING
#include <signal.h>
#endif

/* The largest ROM any supported mapper accepts is 8 MiB (MBC5); the core applies
 * the tighter type-aware ceiling after this host read bound. */
#define PLAYER_SESSION_MAX_ROM_SIZE (8u * 1024u * 1024u)
#define PLAYER_SESSION_MAX_RAM_SIZE 131072u
#define PLAYER_SAVE_HEADER_SIZE 51u
#define PLAYER_SAVE_MAGIC "GBBBSAVE"
#define PLAYER_SAVE_VERSION 1u
#define PLAYER_SAVE_V2_HEADER_SIZE 64u
#define PLAYER_SAVE_V2_VERSION 2u
#define PLAYER_SAVE_V2_MAX_SIZE \
    (PLAYER_SAVE_V2_HEADER_SIZE + PLAYER_SESSION_MAX_RAM_SIZE + GBB_RTC_BLOCK_SIZE)
#define PLAYER_SAVE_V2_FLAG_RTC 0x01u
#define PLAYER_SAVE_V2_FLAG_SAVED_AT 0x02u

#ifdef GBB_PLAYER_SESSION_TESTING
static player_session_test_fault_stage test_fault_stage;
static const char *test_pref_path;
static uint32_t recovery_sequence;

void player_session_test_set_pref_path(const char *path) {
    test_pref_path = path;
}

void player_session_test_set_fault(player_session_test_fault_stage stage) {
    test_fault_stage = stage;
}

static bool consume_test_fault(player_session_test_fault_stage stage) {
    if (test_fault_stage != stage) return false;
    test_fault_stage = PLAYER_SESSION_TEST_FAULT_NONE;
    return true;
}

static void stop_for_test_interrupt(player_session_test_fault_stage stage) {
    if (consume_test_fault(stage)) (void)raise(SIGSTOP);
}
#endif

static void set_error(char *out_error, size_t capacity, const char *message) {
    if (out_error == NULL || capacity == 0u) return;
    (void)snprintf(out_error, capacity, "%s", message);
}

static const char *rom_error(gbb_error error) {
    switch (error) {
    case GBB_ROM_TRUNCATED:
        return "The selected file is truncated; choose a complete supported Game Boy ROM.";
    case GBB_ROM_TOO_LARGE:
        return "The selected file exceeds the largest ROM size supported for its cartridge type.";
    case GBB_ROM_SIZE_MISMATCH:
        return "The selected ROM length does not match its declared size.";
    case GBB_UNSUPPORTED_CARTRIDGE:
        return "This cartridge type is not supported by the current preview.";
    case GBB_UNSUPPORTED_CARTRIDGE_VARIANT:
        return "This MBC1 multicart wiring is not supported by the current preview.";
    case GBB_UNSUPPORTED_ROM_SIZE:
        return "This cartridge ROM size is not supported by the current preview.";
    case GBB_UNSUPPORTED_RAM_SIZE:
        return "This cartridge RAM configuration is not supported by the current preview.";
    case GBB_INVALID_ROM:
        return "The ROM header checksum is invalid.";
    case GBB_OUT_OF_MEMORY:
        return "There is not enough memory to load this ROM.";
    default:
        return "The selected file is not a supported Game Boy ROM.";
    }
}

static bool copy_rom_path(const char *path, char **out_copy,
                          char *out_error, size_t error_capacity) {
    if (path == NULL || path[0] == '\0') {
        set_error(out_error, error_capacity, "No ROM file was selected.");
        return false;
    }
    size_t length = 0u;
    while (length <= PLAYER_SESSION_PATH_LIMIT && path[length] != '\0') ++length;
    if (length > PLAYER_SESSION_PATH_LIMIT) {
        set_error(out_error, error_capacity, "The selected file path is too long.");
        return false;
    }
    char *copy = malloc(length + 1u);
    if (copy == NULL) {
        set_error(out_error, error_capacity, "There is not enough memory to open this ROM.");
        return false;
    }
    memcpy(copy, path, length + 1u);
    *out_copy = copy;
    return true;
}

static bool read_rom_file(const char *path, uint8_t **out_rom, size_t *out_size,
                          char *out_error, size_t error_capacity) {
    /* O_NONBLOCK keeps opening a FIFO or device from blocking; O_NOCTTY keeps a
     * terminal path from becoming the controlling terminal. Different problems,
     * so both flags stay. */
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK | O_NOCTTY);
    if (fd < 0) {
        set_error(out_error, error_capacity, "Could not open the selected ROM file.");
        return false;
    }
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0 ||
        (uintmax_t)info.st_size > (uintmax_t)PLAYER_SESSION_MAX_ROM_SIZE + 1u) {
        (void)close(fd);
        set_error(out_error, error_capacity, "The selected ROM file is not a bounded regular file.");
        return false;
    }
    const size_t capacity = PLAYER_SESSION_MAX_ROM_SIZE + 1u;
    uint8_t *bytes = malloc(capacity);
    if (bytes == NULL) {
        (void)close(fd);
        set_error(out_error, error_capacity, "There is not enough memory to read this ROM.");
        return false;
    }
    size_t total = 0u;
    while (total < capacity) {
        const ssize_t count = read(fd, bytes + total, capacity - total);
        if (count > 0) {
            total += (size_t)count;
            continue;
        }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) {
            free(bytes);
            (void)close(fd);
            set_error(out_error, error_capacity, "Could not read the selected ROM completely.");
            return false;
        }
        break;
    }
    const int close_result = close(fd);
    if (total > PLAYER_SESSION_MAX_ROM_SIZE) {
        free(bytes);
        set_error(out_error, error_capacity, "The selected ROM exceeds the 8 MiB read bound.");
        return false;
    }
    if (close_result != 0) {
        free(bytes);
        set_error(out_error, error_capacity, "Could not finish reading the selected ROM.");
        return false;
    }
    *out_rom = bytes;
    *out_size = total;
    return true;
}

bool player_session_identify_rom(const uint8_t *rom, size_t rom_size,
                                 player_save_identity *out_identity) {
    if (rom == NULL || out_identity == NULL || rom_size < 0x150u ||
        rom_size > PLAYER_SESSION_MAX_ROM_SIZE)
        return false;
    player_save_identity identity;
    memset(&identity, 0, sizeof(identity));
    if (CC_SHA256(rom, (CC_LONG)rom_size, identity.rom_sha256) == NULL)
        return false;
    /* The header byte only names the file and binds the envelope; whether the
     * cartridge has a battery, how much RAM and a clock come from the core. */
    identity.cartridge_type = rom[0x147u];
    *out_identity = identity;
    return true;
}

bool player_session_classify_cartridge(gbb_instance *machine,
                                       player_save_identity *identity) {
    if (machine == NULL || identity == NULL) return false;
    size_t image = 0u;
    const gbb_error size_result = gbb_battery_size(machine, &image);
    identity->battery_backed = false;
    identity->rtc_present = false;
    identity->ram_size = 0u;
    identity->persistence_enabled = false;
    identity->saved_generation = 0u;
    identity->envelope_version = 0u;
    if (size_result == GBB_NO_BATTERY) return true;
    if (size_result != GBB_OK || image == 0u) return false;
    /* A zero-second catch-up is a documented no-op that reports whether the
     * cartridge carries a timer, so the player never guesses from the header. */
    const gbb_error rtc_result = gbb_rtc_catch_up(machine, 0);
    if (rtc_result != GBB_OK && rtc_result != GBB_NO_RTC) return false;
    const bool rtc = rtc_result == GBB_OK;
    if (rtc && image < GBB_RTC_BLOCK_SIZE) return false;
    const size_t ram = image - (rtc ? (size_t)GBB_RTC_BLOCK_SIZE : 0u);
    if (ram > PLAYER_SESSION_MAX_RAM_SIZE) return false;
    identity->rtc_present = rtc;
    identity->ram_size = (uint32_t)ram;
    identity->battery_backed = true;
    identity->persistence_enabled = true;
    return true;
}

void player_session_set_clock(player_save_identity *identity, int64_t now_unix,
                              bool now_valid) {
    if (identity == NULL) return;
    identity->clock_now_unix = now_valid ? now_unix : 0;
    identity->clock_valid = now_valid;
}

bool player_session_replace_rom(gbb_instance *machine, char **in_out_path,
                                const char *path,
                                player_save_identity *out_identity,
                                char *out_error, size_t error_capacity) {
    if (out_error != NULL && error_capacity > 0u) out_error[0] = '\0';
    if (machine == NULL || in_out_path == NULL || out_identity == NULL) {
        set_error(out_error, error_capacity, "The player session is unavailable.");
        return false;
    }
    char *new_path = NULL;
    if (!copy_rom_path(path, &new_path, out_error, error_capacity)) return false;

    uint8_t *rom = NULL;
    size_t rom_size = 0u;
    if (!read_rom_file(path, &rom, &rom_size, out_error, error_capacity)) {
        free(new_path);
        return false;
    }
    if (rom_size < 0x150u) {
        free(rom);
        free(new_path);
        set_error(out_error, error_capacity, rom_error(GBB_ROM_TRUNCATED));
        return false;
    }
    player_save_identity identity;
    if (!player_session_identify_rom(rom, rom_size, &identity)) {
        free(rom);
        free(new_path);
        set_error(out_error, error_capacity, "Could not identify the selected ROM safely.");
        return false;
    }
    const gbb_error result = gbb_load_rom(machine, rom, rom_size);
    free(rom);
    if (result != GBB_OK) {
        set_error(out_error, error_capacity, rom_error(result));
        free(new_path);
        return false;
    }
    if (!player_session_classify_cartridge(machine, &identity)) {
        set_error(out_error, error_capacity, "Could not classify the cartridge battery safely.");
        free(new_path);
        return false;
    }
    free(*in_out_path);
    *in_out_path = new_path;
    *out_identity = identity;
    return true;
}

/* Continues a finished CRC-32 over more bytes: update(crc32(a), b) equals
 * crc32(a followed by b), so the v2 checksum can cover header then payload. */
static uint32_t crc32_update(uint32_t finished, const uint8_t *bytes, size_t size) {
    uint32_t crc = finished ^ UINT32_C(0xFFFFFFFF);
    for (size_t i = 0u; i < size; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint32_t crc32_bytes(const uint8_t *bytes, size_t size) {
    return crc32_update(0u, bytes, size);
}

static void put_u16_le(uint8_t *out, uint16_t value) {
    out[0] = (uint8_t)value;
    out[1] = (uint8_t)(value >> 8);
}

static uint16_t get_u16_le(const uint8_t *bytes) {
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8));
}

static void put_u32_le(uint8_t *out, uint32_t value) {
    for (unsigned i = 0u; i < 4u; ++i) out[i] = (uint8_t)(value >> (i * 8u));
}

static uint32_t get_u32_le(const uint8_t *bytes) {
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

static void put_i64_le(uint8_t *out, int64_t value) {
    const uint64_t bits = (uint64_t)value;
    for (unsigned i = 0u; i < 8u; ++i) out[i] = (uint8_t)(bits >> (i * 8u));
}

static int64_t get_i64_le(const uint8_t *bytes) {
    uint64_t bits = 0u;
    for (unsigned i = 0u; i < 8u; ++i) bits |= (uint64_t)bytes[i] << (i * 8u);
    /* Two's complement reinterpretation; the value range is every int64_t. */
    return (int64_t)bits;
}

static bool ram_length_allowed(uint32_t length) {
    return length == 0u || length == 512u || length == 8192u ||
           length == 32768u || length == 65536u || length == 131072u;
}

/* MBC1 type $03 with 8 or 32 KiB RAM is the only cartridge v0.1 could save. */
static bool v1_eligible(const player_save_identity *identity) {
    return identity->cartridge_type == 0x03u && !identity->rtc_present &&
           (identity->ram_size == 8192u || identity->ram_size == 32768u);
}

static size_t image_size_of(const player_save_identity *identity) {
    return (size_t)identity->ram_size +
           (identity->rtc_present ? (size_t)GBB_RTC_BLOCK_SIZE : 0u);
}

static char *battery_file_path(const player_save_identity *identity) {
    if (identity == NULL || !identity->battery_backed) return NULL;
    char *directory = NULL;
    bool directory_from_sdl = true;
#ifdef GBB_PLAYER_SESSION_TESTING
    if (test_pref_path != NULL) {
        const size_t root_length = strlen(test_pref_path);
        const bool has_separator = root_length > 0u &&
                                   test_pref_path[root_length - 1u] == '/';
        directory = malloc(root_length + (has_separator ? 1u : 2u));
        directory_from_sdl = false;
        if (directory != NULL) {
            memcpy(directory, test_pref_path, root_length);
            size_t directory_index = root_length;
            if (!has_separator) directory[directory_index++] = '/';
            directory[directory_index] = '\0';
        }
    } else
#endif
    {
        directory = SDL_GetPrefPath("GabbaBoy", "GabbaBoy");
    }
    if (directory == NULL) return NULL;
    const size_t directory_length = strlen(directory);
    if (directory_length > PLAYER_SESSION_PATH_LIMIT) {
        if (directory_from_sdl) SDL_free(directory);
        else free(directory);
        return NULL;
    }
    char digest[65];
    static const char hex[] = "0123456789abcdef";
    for (size_t i = 0u; i < sizeof(identity->rom_sha256); ++i) {
        digest[i * 2u] = hex[identity->rom_sha256[i] >> 4];
        digest[i * 2u + 1u] = hex[identity->rom_sha256[i] & 0x0Fu];
    }
    digest[64] = '\0';
    char suffix[32];
    const int suffix_length = snprintf(suffix, sizeof(suffix),
                                       identity->cartridge_type == 0x03u
                                           ? "-mbc1-%02x-%08x.gbb"
                                           : "-cart-%02x-%08x.gbb",
                                       identity->cartridge_type,
                                       identity->ram_size);
    if (suffix_length < 0 || (size_t)suffix_length >= sizeof(suffix) ||
        directory_length > PLAYER_SESSION_PATH_LIMIT - (size_t)suffix_length - 65u) {
        if (directory_from_sdl) SDL_free(directory);
        else free(directory);
        return NULL;
    }
    const size_t path_length = directory_length + 64u + (size_t)suffix_length;
    if (path_length > PLAYER_SESSION_PATH_LIMIT - 64u) {
        if (directory_from_sdl) SDL_free(directory);
        else free(directory);
        return NULL;
    }
    char *path = malloc(path_length + 1u);
    if (path != NULL) {
        memcpy(path, directory, directory_length);
        memcpy(path + directory_length, digest, 64u);
        memcpy(path + directory_length + 64u, suffix, (size_t)suffix_length + 1u);
    }
    if (directory_from_sdl) SDL_free(directory);
    else free(directory);
    return path;
}

#ifdef GBB_PLAYER_SESSION_TESTING
char *player_session_test_battery_file_path(
    const player_save_identity *identity) {
    return battery_file_path(identity);
}
#endif

static bool read_save_file(const char *path, uint8_t *bytes, size_t capacity,
                           size_t *out_size, bool *out_missing,
                           bool *out_recoverable, struct stat *out_info) {
    *out_missing = false;
    *out_recoverable = false;
    *out_size = 0u;
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) {
        if (errno == ENOENT) {
            *out_missing = true;
            return true;
        }
        return false;
    }
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0) {
        (void)close(fd);
        return false;
    }
    *out_info = info;
    *out_recoverable = true;
    if ((uintmax_t)info.st_size > capacity) {
        (void)close(fd);
        return false;
    }
    size_t total = 0u;
    while (total < capacity) {
        const ssize_t count = read(fd, bytes + total, capacity - total);
        if (count > 0) {
            total += (size_t)count;
            continue;
        }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) {
            (void)close(fd);
            return false;
        }
        break;
    }
    struct stat after;
    const bool stable = fstat(fd, &after) == 0 &&
                        after.st_dev == info.st_dev &&
                        after.st_ino == info.st_ino &&
                        after.st_size == info.st_size &&
                        total == (size_t)info.st_size;
    const int close_result = close(fd);
    if (!stable || close_result != 0) return false;
    *out_size = total;
    return true;
}

static bool sync_save_directory(const char *path);

static bool same_file_identity(const struct stat *left,
                               const struct stat *right) {
    return S_ISREG(right->st_mode) && left->st_dev == right->st_dev &&
           left->st_ino == right->st_ino;
}

static bool preserve_rejected_save(const char *path,
                                   const struct stat *expected_info) {
    struct stat current_info;
    if (lstat(path, &current_info) != 0 ||
        !same_file_identity(expected_info, &current_info))
        return false;

    char recovery_path[PLAYER_SESSION_PATH_LIMIT + 1u];
    const size_t path_length = strlen(path);
    for (unsigned attempt = 0u; attempt < 100u; ++attempt) {
#ifdef GBB_PLAYER_SESSION_TESTING
        ++recovery_sequence;
        if (recovery_sequence == 0u) ++recovery_sequence;
        const uint32_t sequence = recovery_sequence;
#else
        const uint32_t sequence = (uint32_t)attempt + 1u;
#endif
        char suffix[48];
        const int written = snprintf(suffix, sizeof(suffix),
                                     ".recovery-%ld-%08x",
                                     (long)getpid(), sequence);
        if (written < 0 || (size_t)written >= sizeof(suffix) ||
            path_length + (size_t)written > PLAYER_SESSION_PATH_LIMIT)
            return false;
        memcpy(recovery_path, path, path_length);
        memcpy(recovery_path + path_length, suffix, (size_t)written + 1u);
#ifdef GBB_PLAYER_SESSION_TESTING
        if (consume_test_fault(PLAYER_SESSION_TEST_FAULT_RECOVERY_RENAME)) {
            errno = EIO;
            return false;
        }
#endif
        if (renameatx_np(AT_FDCWD, path, AT_FDCWD, recovery_path,
                         RENAME_EXCL) == 0) {
            if (sync_save_directory(recovery_path)) return true;
            (void)renameatx_np(AT_FDCWD, recovery_path, AT_FDCWD, path,
                               RENAME_EXCL);
            return false;
        }
        if (errno != EEXIST) return false;
    }
    return false;
}

/* v1 (MBC1 $03 only): validates size, identity and checksum, then copies RAM. */
static bool decode_save_v1(const uint8_t *bytes, size_t size,
                           const player_save_identity *identity,
                           uint8_t *out_image) {
    if (!v1_eligible(identity) ||
        size != (size_t)PLAYER_SAVE_HEADER_SIZE + identity->ram_size ||
        memcmp(bytes, PLAYER_SAVE_MAGIC, 8u) != 0 ||
        get_u16_le(bytes + 8u) != PLAYER_SAVE_VERSION ||
        memcmp(bytes + 10u, identity->rom_sha256, 32u) != 0 ||
        bytes[42u] != identity->cartridge_type ||
        get_u32_le(bytes + 43u) != identity->ram_size ||
        get_u32_le(bytes + 47u) != crc32_bytes(bytes + PLAYER_SAVE_HEADER_SIZE,
                                                identity->ram_size))
        return false;
    memcpy(out_image, bytes + PLAYER_SAVE_HEADER_SIZE, identity->ram_size);
    return true;
}

/* v2 header, little-endian, written and read field by field:
 *   0-7 magic, 8-9 version 2, 10-41 ROM SHA-256, 42 type, 43 flags (bit0 RTC
 *   block present, bit1 saved_at valid and only with bit0), 44-47 ram_len,
 *   48-51 rtc_len, 52-59 saved_at (i64, zero unless bit1), 60-63 CRC-32 over
 *   bytes 0-59 then the payload. Payload is RAM followed by the RTC block.
 * Every length is checked against its allow-list before any addition, the
 * total is formed in uint64_t, and nothing is copied until every check passed. */
static bool decode_save_v2(const uint8_t *bytes, size_t size,
                           const player_save_identity *identity,
                           uint8_t *out_image, int64_t *out_saved_at,
                           bool *out_saved_valid) {
    if (size < PLAYER_SAVE_V2_HEADER_SIZE ||
        memcmp(bytes, PLAYER_SAVE_MAGIC, 8u) != 0 ||
        get_u16_le(bytes + 8u) != PLAYER_SAVE_V2_VERSION ||
        memcmp(bytes + 10u, identity->rom_sha256, 32u) != 0 ||
        bytes[42u] != identity->cartridge_type)
        return false;
    const uint8_t flags = bytes[43u];
    const uint32_t ram_len = get_u32_le(bytes + 44u);
    const uint32_t rtc_len = get_u32_le(bytes + 48u);
    const int64_t saved_at = get_i64_le(bytes + 52u);
    const bool has_rtc = (flags & PLAYER_SAVE_V2_FLAG_RTC) != 0u;
    const bool has_saved_at = (flags & PLAYER_SAVE_V2_FLAG_SAVED_AT) != 0u;
    if ((flags & ~(PLAYER_SAVE_V2_FLAG_RTC | PLAYER_SAVE_V2_FLAG_SAVED_AT)) != 0u ||
        (has_saved_at && !has_rtc) ||
        !ram_length_allowed(ram_len) ||
        (rtc_len != 0u && rtc_len != GBB_RTC_BLOCK_SIZE) ||
        has_rtc != (rtc_len == GBB_RTC_BLOCK_SIZE) ||
        ram_len != identity->ram_size ||
        (rtc_len != 0u) != identity->rtc_present ||
        (!has_saved_at && saved_at != 0))
        return false;
    const uint64_t total = (uint64_t)PLAYER_SAVE_V2_HEADER_SIZE +
                           (uint64_t)ram_len + (uint64_t)rtc_len;
    if (total != (uint64_t)size) return false;
    const uint32_t crc = crc32_update(crc32_bytes(bytes, 60u),
                                      bytes + PLAYER_SAVE_V2_HEADER_SIZE,
                                      (size_t)ram_len + rtc_len);
    if (get_u32_le(bytes + 60u) != crc) return false;
    memcpy(out_image, bytes + PLAYER_SAVE_V2_HEADER_SIZE,
           (size_t)ram_len + rtc_len);
    *out_saved_at = has_saved_at ? saved_at : 0;
    *out_saved_valid = has_saved_at;
    return true;
}

static bool load_failure(player_save_identity *identity, char *path,
                         uint8_t *bytes, uint8_t *image, char *out_error,
                         size_t error_capacity, const char *message) {
    free(path);
    free(bytes);
    free(image);
    identity->persistence_enabled = false;
    set_error(out_error, error_capacity, message);
    return false;
}

bool player_session_load_battery(gbb_instance *machine,
                                 player_save_identity *identity,
                                 char *out_error, size_t error_capacity) {
    if (out_error != NULL && error_capacity > 0u) out_error[0] = '\0';
    if (machine == NULL || identity == NULL) {
        set_error(out_error, error_capacity, "The player session is unavailable.");
        return false;
    }
    if (!identity->battery_backed) return true;
    size_t core_image = 0u;
    const size_t image_size = image_size_of(identity);
    if (gbb_battery_size(machine, &core_image) != GBB_OK ||
        core_image != image_size ||
        !ram_length_allowed(identity->ram_size) ||
        identity->ram_size > PLAYER_SESSION_MAX_RAM_SIZE) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "Battery RAM does not match the loaded cartridge.");
        return false;
    }
    char *path = battery_file_path(identity);
    if (path == NULL) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The per-user save directory is unavailable.");
        return false;
    }
    const size_t capacity = (size_t)PLAYER_SAVE_V2_MAX_SIZE + 1u;
    uint8_t *bytes = malloc(capacity);
    uint8_t *image = malloc(image_size);
    if (bytes == NULL || image == NULL)
        return load_failure(identity, path, bytes, image, out_error,
                            error_capacity, "There is not enough memory to read the save.");
    size_t file_size = 0u;
    bool missing = false;
    bool recoverable = false;
    struct stat file_info;
    const bool read_ok = read_save_file(path, bytes, capacity, &file_size,
                                        &missing, &recoverable, &file_info);
    if (!read_ok && !recoverable)
        return load_failure(identity, path, bytes, image, out_error, error_capacity,
                            "The existing save could not be read safely; persistence is disabled.");
    if (missing) {
        free(path);
        free(bytes);
        free(image);
        identity->saved_generation = 0u;
        identity->envelope_version = 0u;
        identity->persistence_enabled = true;
        return true;
    }
    uint8_t version = 0u;
    int64_t saved_at = 0;
    bool saved_valid = false;
    if (read_ok) {
        if (decode_save_v1(bytes, file_size, identity, image)) version = 1u;
        else if (decode_save_v2(bytes, file_size, identity, image, &saved_at,
                                &saved_valid)) version = 2u;
    }
    (void)saved_at;
    (void)saved_valid;
    if (version != 0u) {
        if (gbb_import_battery(machine, image, image_size) != GBB_OK)
            return load_failure(identity, path, bytes, image, out_error, error_capacity,
                                "The valid save could not be imported; the original file was left untouched.");
        free(path);
        free(bytes);
        free(image);
        if (gbb_battery_generation(machine, &identity->saved_generation) != GBB_OK) {
            identity->persistence_enabled = false;
            set_error(out_error, error_capacity, "Could not record the loaded battery generation.");
            return false;
        }
        identity->envelope_version = version;
        identity->persistence_enabled = true;
        return true;
    }
    const bool preserved = recoverable && preserve_rejected_save(path, &file_info);
    free(path);
    free(bytes);
    if (!preserved) {
        free(image);
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The existing save could not be preserved; battery saving is disabled.");
        return false;
    }
    /* Fresh RAM is all $FF; a timer keeps the clock the core already holds. */
    const bool have_image = gbb_copy_battery(machine, image, image_size) == GBB_OK;
    if (have_image) memset(image, 0xFF, identity->ram_size);
    const bool fresh = have_image &&
                       gbb_import_battery(machine, image, image_size) == GBB_OK;
    free(image);
    if (!fresh) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The rejected save was preserved, but fresh battery RAM could not be initialized.");
        return false;
    }
    if (gbb_battery_generation(machine, &identity->saved_generation) != GBB_OK) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The rejected save was preserved, but battery state could not be recorded.");
        return false;
    }
    identity->envelope_version = 0u;
    identity->persistence_enabled = true;
    set_error(out_error, error_capacity, "The existing save was rejected and preserved; fresh RAM is active.");
    return false;
}

static bool write_all(int fd, const uint8_t *bytes, size_t size) {
    size_t written = 0u;
#ifdef GBB_PLAYER_SESSION_TESTING
    const bool inject_short_write =
        consume_test_fault(PLAYER_SESSION_TEST_FAULT_SHORT_WRITE);
    const size_t stop_after = size / 2u;
#endif
    while (written < size) {
        size_t remaining = size - written;
#ifdef GBB_PLAYER_SESSION_TESTING
        if (inject_short_write && written < stop_after &&
            remaining > stop_after - written)
            remaining = stop_after - written;
        if (inject_short_write && written >= stop_after) {
            errno = EIO;
            return false;
        }
#endif
        const ssize_t count = write(fd, bytes + written, remaining);
        if (count > 0) {
            written += (size_t)count;
            continue;
        }
        if (count < 0 && errno == EINTR) continue;
        return false;
    }
    return true;
}

static bool sync_save_directory(const char *path) {
#ifdef GBB_PLAYER_SESSION_TESTING
    if (consume_test_fault(PLAYER_SESSION_TEST_FAULT_DIRECTORY_SYNC)) {
        errno = EIO;
        return false;
    }
#endif
    char directory[PLAYER_SESSION_PATH_LIMIT + 1u];
    const size_t length = strlen(path);
    if (length == 0u || length > PLAYER_SESSION_PATH_LIMIT) return false;
    memcpy(directory, path, length + 1u);
    char *separator = strrchr(directory, '/');
    if (separator == NULL) return false;
    if (separator == directory) separator[1] = '\0';
    else *separator = '\0';
    const int fd = open(directory, O_RDONLY | O_CLOEXEC | O_DIRECTORY);
    if (fd < 0) return false;
    const int result = fsync(fd);
    const int saved_errno = errno;
    (void)close(fd);
    if (result == 0 || saved_errno == EINVAL || saved_errno == ENOTSUP ||
        saved_errno == EOPNOTSUPP)
        return true;
    return false;
}

static bool save_target_is_replaceable(const char *path) {
    struct stat info;
    if (lstat(path, &info) == 0) {
        if (S_ISREG(info.st_mode) && !S_ISLNK(info.st_mode)) return true;
        errno = EINVAL;
        return false;
    }
    return errno == ENOENT;
}

static bool atomic_save(const char *path, const uint8_t *bytes, size_t size) {
    const size_t path_length = strlen(path);
    static const char suffix[] = ".tmp.XXXXXX";
    if (path_length > PLAYER_SESSION_PATH_LIMIT - (sizeof(suffix) - 1u)) return false;
    if (!save_target_is_replaceable(path)) return false;
    char temporary[PLAYER_SESSION_PATH_LIMIT + 1u];
    memcpy(temporary, path, path_length);
    memcpy(temporary + path_length, suffix, sizeof(suffix));
#ifdef GBB_PLAYER_SESSION_TESTING
    const bool fail_temp_create =
        consume_test_fault(PLAYER_SESSION_TEST_FAULT_TEMP_CREATE);
#else
    const bool fail_temp_create = false;
#endif
    const int fd = fail_temp_create ? -1 : mkstemp(temporary);
    if (fail_temp_create) errno = EIO;
    if (fd < 0) {
        fprintf(stderr, "Battery save temporary creation failed: %s\n",
                strerror(errno));
        return false;
    }
    const char *failed_at = NULL;
    int failure_errno = 0;
    bool ok = fchmod(fd, S_IRUSR | S_IWUSR) == 0;
    if (!ok) { failed_at = "permissions"; failure_errno = errno; }
    if (ok && !write_all(fd, bytes, size)) {
        ok = false; failed_at = "write"; failure_errno = errno;
    }
#ifdef GBB_PLAYER_SESSION_TESTING
    const bool fail_file_sync =
        consume_test_fault(PLAYER_SESSION_TEST_FAULT_FILE_SYNC);
#else
    const bool fail_file_sync = false;
#endif
    if (ok && (fail_file_sync || fsync(fd) != 0)) {
        if (fail_file_sync) errno = EIO;
        ok = false; failed_at = "file sync"; failure_errno = errno;
    }
    if (close(fd) != 0 && ok) {
        ok = false; failed_at = "close"; failure_errno = errno;
    }
#ifdef GBB_PLAYER_SESSION_TESTING
    stop_for_test_interrupt(PLAYER_SESSION_TEST_INTERRUPT_BEFORE_RENAME);
    const bool fail_rename = consume_test_fault(PLAYER_SESSION_TEST_FAULT_RENAME);
#else
    const bool fail_rename = false;
#endif
    if (ok && !save_target_is_replaceable(path)) {
        ok = false; failed_at = "target validation"; failure_errno = errno;
    }
    if (ok && (fail_rename || rename(temporary, path) != 0)) {
        if (fail_rename) errno = EIO;
        ok = false; failed_at = "rename"; failure_errno = errno;
    }
#ifdef GBB_PLAYER_SESSION_TESTING
    if (ok) stop_for_test_interrupt(PLAYER_SESSION_TEST_INTERRUPT_AFTER_RENAME);
#endif
    if (ok && !sync_save_directory(path)) {
        ok = false; failed_at = "directory sync"; failure_errno = errno;
    }
    if (!ok) (void)unlink(temporary);
    if (!ok)
        fprintf(stderr, "Battery save %s failed: %s\n", failed_at,
                strerror(failure_errno));
    return ok;
}

bool player_session_save_battery(gbb_instance *machine,
                                 player_save_identity *identity,
                                 char *out_error, size_t error_capacity) {
    if (out_error != NULL && error_capacity > 0u) out_error[0] = '\0';
    if (machine == NULL || identity == NULL) {
        set_error(out_error, error_capacity, "The player session is unavailable.");
        return false;
    }
    if (!identity->battery_backed) return true;
    if (!identity->persistence_enabled) {
        set_error(out_error, error_capacity, "Battery saving is disabled because the existing save was not accepted.");
        return false;
    }
    size_t core_image = 0u;
    const size_t image_size = image_size_of(identity);
    uint64_t generation = 0u;
    if (gbb_battery_size(machine, &core_image) != GBB_OK ||
        gbb_battery_generation(machine, &generation) != GBB_OK ||
        core_image != image_size ||
        !ram_length_allowed(identity->ram_size) ||
        identity->ram_size > PLAYER_SESSION_MAX_RAM_SIZE) {
        set_error(out_error, error_capacity, "Battery RAM does not match the active cartridge.");
        return false;
    }
    if (generation == identity->saved_generation) return true;
    /* The version is a function of the cartridge type and of the version of the
     * file that was loaded: v1 stays v1 for MBC1 $03, and a $03 save that was
     * read from v2 is never written back as v1. */
    const bool write_v1 = v1_eligible(identity) && identity->envelope_version != 2u;
    const size_t header = write_v1 ? PLAYER_SAVE_HEADER_SIZE
                                   : PLAYER_SAVE_V2_HEADER_SIZE;
    uint8_t *bytes = malloc(header + image_size);
    if (bytes == NULL) {
        set_error(out_error, error_capacity, "There is not enough memory to save battery RAM.");
        return false;
    }
    memset(bytes, 0, header);
    memcpy(bytes, PLAYER_SAVE_MAGIC, 8u);
    memcpy(bytes + 10u, identity->rom_sha256, 32u);
    bytes[42u] = identity->cartridge_type;
    if (gbb_copy_battery(machine, bytes + header, image_size) != GBB_OK) {
        free(bytes);
        set_error(out_error, error_capacity, "Could not copy battery RAM safely.");
        return false;
    }
    if (write_v1) {
        put_u16_le(bytes + 8u, PLAYER_SAVE_VERSION);
        put_u32_le(bytes + 43u, (uint32_t)identity->ram_size);
        put_u32_le(bytes + 47u,
                   crc32_bytes(bytes + PLAYER_SAVE_HEADER_SIZE, identity->ram_size));
    } else {
        /* The RTC block was exported just now, so saved_at stamps the same instant. */
        const bool stamp = identity->rtc_present && identity->clock_valid;
        put_u16_le(bytes + 8u, PLAYER_SAVE_V2_VERSION);
        bytes[43u] = (uint8_t)((identity->rtc_present ? PLAYER_SAVE_V2_FLAG_RTC : 0u) |
                               (stamp ? PLAYER_SAVE_V2_FLAG_SAVED_AT : 0u));
        put_u32_le(bytes + 44u, identity->ram_size);
        put_u32_le(bytes + 48u, identity->rtc_present ? GBB_RTC_BLOCK_SIZE : 0u);
        put_i64_le(bytes + 52u, stamp ? identity->clock_now_unix : 0);
        put_u32_le(bytes + 60u,
                   crc32_update(crc32_bytes(bytes, 60u),
                                bytes + PLAYER_SAVE_V2_HEADER_SIZE, image_size));
    }
    char *path = battery_file_path(identity);
    if (path == NULL) {
        free(bytes);
        set_error(out_error, error_capacity, "The per-user save directory is unavailable.");
        return false;
    }
    const bool saved = atomic_save(path, bytes, header + image_size);
    free(path);
    free(bytes);
    if (!saved) {
        set_error(out_error, error_capacity, "Could not atomically save battery RAM; progress remains in memory.");
        return false;
    }
    identity->saved_generation = generation;
    identity->envelope_version = write_v1 ? 1u : 2u;
    return true;
}

static char *battery_lock_file_path(const player_save_identity *identity) {
    char *save_path = battery_file_path(identity);
    if (save_path == NULL) return NULL;
    const size_t length = strlen(save_path);
    static const char suffix[] = ".lock";
    if (length > PLAYER_SESSION_PATH_LIMIT - (sizeof(suffix) - 1u)) {
        free(save_path);
        return NULL;
    }
    char *lock_path = malloc(length + sizeof(suffix));
    if (lock_path != NULL) {
        memcpy(lock_path, save_path, length);
        memcpy(lock_path + length, suffix, sizeof(suffix));
    }
    free(save_path);
    return lock_path;
}

player_session_lock_result player_session_lock_battery(
    const player_save_identity *identity, int *out_lock_fd,
    char *out_error, size_t error_capacity) {
    if (out_error != NULL && error_capacity > 0u) out_error[0] = '\0';
    if (identity == NULL || out_lock_fd == NULL) {
        set_error(out_error, error_capacity, "The player session is unavailable.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
    *out_lock_fd = -1;
    if (!identity->battery_backed) return PLAYER_SESSION_LOCK_ACQUIRED;
    char *path = battery_lock_file_path(identity);
    if (path == NULL) {
        set_error(out_error, error_capacity, "The per-user save directory is unavailable.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
    const int fd = open(path, O_RDWR | O_CREAT | O_CLOEXEC | O_NOFOLLOW,
                        S_IRUSR | S_IWUSR);
    if (fd < 0) {
        free(path);
        set_error(out_error, error_capacity, "Could not open the battery session lock safely.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
    struct stat opened_info, path_info;
    if (fstat(fd, &opened_info) != 0 || !S_ISREG(opened_info.st_mode) ||
        lstat(path, &path_info) != 0 ||
        !same_file_identity(&opened_info, &path_info)) {
        (void)close(fd);
        free(path);
        set_error(out_error, error_capacity, "The battery session lock is not a stable regular file.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
    free(path);
#ifdef GBB_PLAYER_SESSION_TESTING
    if (consume_test_fault(PLAYER_SESSION_TEST_FAULT_LOCK_ACQUIRE)) {
        errno = EIO;
        (void)close(fd);
        set_error(out_error, error_capacity, "Could not acquire the battery session lock.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
#endif
    if (flock(fd, LOCK_EX | LOCK_NB) != 0) {
        const int lock_errno = errno;
        (void)close(fd);
        if (lock_errno == EWOULDBLOCK || lock_errno == EAGAIN) {
            set_error(out_error, error_capacity,
                      "Another GabbaBoy process is using this battery save.");
            return PLAYER_SESSION_LOCK_BUSY;
        }
        set_error(out_error, error_capacity,
                  "Could not acquire the battery session lock.");
        return PLAYER_SESSION_LOCK_ERROR;
    }
    *out_lock_fd = fd;
    return PLAYER_SESSION_LOCK_ACQUIRED;
}

void player_session_unlock_battery(int *in_out_lock_fd) {
    if (in_out_lock_fd == NULL || *in_out_lock_fd < 0) return;
    (void)flock(*in_out_lock_fd, LOCK_UN);
    (void)close(*in_out_lock_fd);
    *in_out_lock_fd = -1;
}

void player_save_cadence_reset(player_save_cadence *cadence,
                               uint64_t generation) {
    if (cadence == NULL) return;
    cadence->observed_generation = generation;
    cadence->first_dirty_ns = 0u;
    cadence->last_change_ns = 0u;
    cadence->dirty = false;
}

bool player_save_cadence_observe(player_save_cadence *cadence,
                                 uint64_t generation,
                                 uint64_t saved_generation,
                                 uint64_t host_time_ns) {
    if (cadence == NULL) return false;
    if (generation == saved_generation) {
        player_save_cadence_reset(cadence, generation);
        return false;
    }
    if (!cadence->dirty) {
        cadence->dirty = true;
        cadence->observed_generation = generation;
        cadence->first_dirty_ns = host_time_ns;
        cadence->last_change_ns = host_time_ns;
    } else if (generation != cadence->observed_generation) {
        cadence->observed_generation = generation;
        cadence->last_change_ns = host_time_ns;
    }
    const bool quiet_elapsed = host_time_ns >= cadence->last_change_ns &&
        host_time_ns - cadence->last_change_ns >= UINT64_C(2000000000);
    const bool maximum_age_elapsed = host_time_ns >= cadence->first_dirty_ns &&
        host_time_ns - cadence->first_dirty_ns >= UINT64_C(10000000000);
    return quiet_elapsed || maximum_age_elapsed;
}

player_save_transition_result player_save_transition_resolve(
    bool battery_backed, bool save_succeeded,
    player_save_transition_choice choice) {
    if (!battery_backed || save_succeeded)
        return PLAYER_SAVE_TRANSITION_SAVED;
    switch (choice) {
    case PLAYER_SAVE_TRANSITION_CONTINUE:
        return PLAYER_SAVE_TRANSITION_CONTINUE_UNSAVED;
    case PLAYER_SAVE_TRANSITION_CANCEL:
        return PLAYER_SAVE_TRANSITION_CANCELLED;
    case PLAYER_SAVE_TRANSITION_RETRY:
    default:
        return PLAYER_SAVE_TRANSITION_WAIT;
    }
}

void player_session_remove_battery_file(const player_save_identity *identity) {
    char *path = battery_file_path(identity);
    if (path != NULL) {
        (void)unlink(path);
        free(path);
    }
    path = battery_lock_file_path(identity);
    if (path != NULL) {
        (void)unlink(path);
        free(path);
    }
}
