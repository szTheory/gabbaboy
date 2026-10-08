#include "session.h"

#include <CommonCrypto/CommonDigest.h>
#include <SDL3/SDL.h>

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define PLAYER_SESSION_MAX_ROM_SIZE (2u * 1024u * 1024u)
#define PLAYER_SESSION_MAX_RAM_SIZE 32768u
#define PLAYER_SAVE_HEADER_SIZE 51u
#define PLAYER_SAVE_MAX_SIZE (PLAYER_SAVE_HEADER_SIZE + PLAYER_SESSION_MAX_RAM_SIZE)
#define PLAYER_SAVE_MAGIC "GBBBSAVE"
#define PLAYER_SAVE_VERSION 1u

static void set_error(char *out_error, size_t capacity, const char *message) {
    if (out_error == NULL || capacity == 0u) return;
    (void)snprintf(out_error, capacity, "%s", message);
}

static const char *rom_error(gbb_error error) {
    switch (error) {
    case GBB_ROM_TRUNCATED:
        return "The selected file is truncated; choose a complete supported Game Boy ROM.";
    case GBB_ROM_TOO_LARGE:
        return "The selected file exceeds the supported 2 MiB ROM size.";
    case GBB_ROM_SIZE_MISMATCH:
        return "The selected ROM length does not match its declared size.";
    case GBB_UNSUPPORTED_CARTRIDGE:
        return "This cartridge type is not supported by the current preview.";
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
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
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
    if (close_result != 0 || total > PLAYER_SESSION_MAX_ROM_SIZE) {
        free(bytes);
        set_error(out_error, error_capacity, "The selected ROM exceeds the 2 MiB read bound.");
        return false;
    }
    *out_rom = bytes;
    *out_size = total;
    return true;
}

bool player_session_identify_rom(const uint8_t *rom, size_t rom_size,
                                 player_save_identity *out_identity) {
    if (rom == NULL || out_identity == NULL || rom_size < 0x150u ||
        rom_size > PLAYER_SESSION_MAX_ROM_SIZE ||
        CC_SHA256(rom, (CC_LONG)rom_size, out_identity->rom_sha256) == NULL)
        return false;
    out_identity->cartridge_type = rom[0x147u];
    out_identity->ram_size = rom[0x149u] == 0x02u ? 8192u :
                             rom[0x149u] == 0x03u ? 32768u : 0u;
    out_identity->battery_backed = rom[0x147u] == 0x03u &&
                                   out_identity->ram_size != 0u;
    out_identity->saved_generation = 0u;
    out_identity->persistence_enabled = out_identity->battery_backed;
    return true;
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
    free(*in_out_path);
    *in_out_path = new_path;
    *out_identity = identity;
    return true;
}

static uint32_t crc32_bytes(const uint8_t *bytes, size_t size) {
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (size_t i = 0u; i < size; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? UINT32_C(0xEDB88320) : 0u);
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
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

static char *battery_file_path(const player_save_identity *identity) {
    if (identity == NULL || !identity->battery_backed) return NULL;
    char *directory = SDL_GetPrefPath("GabbaBoy", "GabbaBoy");
    if (directory == NULL) return NULL;
    const size_t directory_length = strlen(directory);
    if (directory_length > PLAYER_SESSION_PATH_LIMIT) {
        SDL_free(directory);
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
    const int suffix_length = snprintf(suffix, sizeof(suffix), "-%02x-%08x.gbb",
                                       identity->cartridge_type,
                                       identity->ram_size);
    if (suffix_length < 0 || (size_t)suffix_length >= sizeof(suffix) ||
        directory_length > PLAYER_SESSION_PATH_LIMIT - (size_t)suffix_length - 65u) {
        SDL_free(directory);
        return NULL;
    }
    const size_t path_length = directory_length + 64u + (size_t)suffix_length;
    char *path = malloc(path_length + 1u);
    if (path != NULL) {
        memcpy(path, directory, directory_length);
        memcpy(path + directory_length, digest, 64u);
        memcpy(path + directory_length + 64u, suffix, (size_t)suffix_length + 1u);
    }
    SDL_free(directory);
    return path;
}

static bool read_save_file(const char *path, uint8_t *bytes, size_t capacity,
                           size_t *out_size, bool *out_missing) {
    *out_missing = false;
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        if (errno == ENOENT) {
            *out_missing = true;
            return true;
        }
        return false;
    }
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0 ||
        (uintmax_t)info.st_size > capacity) {
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
    const int close_result = close(fd);
    if (close_result != 0) return false;
    *out_size = total;
    return true;
}

static bool decode_save(const uint8_t *bytes, size_t size,
                        const player_save_identity *identity,
                        uint8_t *out_ram) {
    if (size != PLAYER_SAVE_HEADER_SIZE + identity->ram_size ||
        memcmp(bytes, PLAYER_SAVE_MAGIC, 8u) != 0 ||
        get_u16_le(bytes + 8u) != PLAYER_SAVE_VERSION ||
        memcmp(bytes + 10u, identity->rom_sha256, 32u) != 0 ||
        bytes[42u] != identity->cartridge_type ||
        get_u32_le(bytes + 43u) != identity->ram_size ||
        get_u32_le(bytes + 47u) != crc32_bytes(bytes + PLAYER_SAVE_HEADER_SIZE,
                                                identity->ram_size))
        return false;
    memcpy(out_ram, bytes + PLAYER_SAVE_HEADER_SIZE, identity->ram_size);
    return true;
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
    size_t ram_size = 0u;
    if (gbb_battery_size(machine, &ram_size) != GBB_OK ||
        ram_size != identity->ram_size || ram_size > PLAYER_SESSION_MAX_RAM_SIZE) {
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
    uint8_t bytes[PLAYER_SAVE_MAX_SIZE + 1u];
    size_t file_size = 0u;
    bool missing = false;
    if (!read_save_file(path, bytes, sizeof(bytes), &file_size, &missing)) {
        free(path);
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The existing save could not be read safely; persistence is disabled.");
        return false;
    }
    free(path);
    if (missing) {
        identity->saved_generation = 0u;
        identity->persistence_enabled = true;
        return true;
    }
    uint8_t ram[PLAYER_SESSION_MAX_RAM_SIZE];
    if (!decode_save(bytes, file_size, identity, ram) ||
        gbb_import_battery(machine, ram, ram_size) != GBB_OK) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "The existing save is invalid or belongs to a different cartridge; persistence is disabled.");
        return false;
    }
    if (gbb_battery_generation(machine, &identity->saved_generation) != GBB_OK) {
        identity->persistence_enabled = false;
        set_error(out_error, error_capacity, "Could not record the loaded battery generation.");
        return false;
    }
    identity->persistence_enabled = true;
    return true;
}

static bool write_all(int fd, const uint8_t *bytes, size_t size) {
    size_t written = 0u;
    while (written < size) {
        const ssize_t count = write(fd, bytes + written, size - written);
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

static bool atomic_save(const char *path, const uint8_t *bytes, size_t size) {
    const size_t path_length = strlen(path);
    static const char suffix[] = ".tmp.XXXXXX";
    if (path_length > PLAYER_SESSION_PATH_LIMIT - (sizeof(suffix) - 1u)) return false;
    char temporary[PLAYER_SESSION_PATH_LIMIT + 1u];
    memcpy(temporary, path, path_length);
    memcpy(temporary + path_length, suffix, sizeof(suffix));
    const int fd = mkstemp(temporary);
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
    if (ok && fsync(fd) != 0) {
        ok = false; failed_at = "file sync"; failure_errno = errno;
    }
    if (close(fd) != 0 && ok) {
        ok = false; failed_at = "close"; failure_errno = errno;
    }
    if (ok && rename(temporary, path) != 0) {
        ok = false; failed_at = "rename"; failure_errno = errno;
    }
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
    size_t ram_size = 0u;
    uint64_t generation = 0u;
    if (gbb_battery_size(machine, &ram_size) != GBB_OK ||
        gbb_battery_generation(machine, &generation) != GBB_OK ||
        ram_size != identity->ram_size || ram_size > PLAYER_SESSION_MAX_RAM_SIZE) {
        set_error(out_error, error_capacity, "Battery RAM does not match the active cartridge.");
        return false;
    }
    if (generation == identity->saved_generation) return true;
    uint8_t bytes[PLAYER_SAVE_HEADER_SIZE + PLAYER_SESSION_MAX_RAM_SIZE];
    memcpy(bytes, PLAYER_SAVE_MAGIC, 8u);
    put_u16_le(bytes + 8u, PLAYER_SAVE_VERSION);
    memcpy(bytes + 10u, identity->rom_sha256, 32u);
    bytes[42u] = identity->cartridge_type;
    put_u32_le(bytes + 43u, (uint32_t)ram_size);
    if (gbb_copy_battery(machine, bytes + PLAYER_SAVE_HEADER_SIZE, ram_size) != GBB_OK) {
        set_error(out_error, error_capacity, "Could not copy battery RAM safely.");
        return false;
    }
    put_u32_le(bytes + 47u,
               crc32_bytes(bytes + PLAYER_SAVE_HEADER_SIZE, ram_size));
    char *path = battery_file_path(identity);
    if (path == NULL) {
        set_error(out_error, error_capacity, "The per-user save directory is unavailable.");
        return false;
    }
    const bool saved = atomic_save(path, bytes, PLAYER_SAVE_HEADER_SIZE + ram_size);
    free(path);
    if (!saved) {
        set_error(out_error, error_capacity, "Could not atomically save battery RAM; progress remains in memory.");
        return false;
    }
    identity->saved_generation = generation;
    return true;
}

void player_session_remove_battery_file(const player_save_identity *identity) {
    char *path = battery_file_path(identity);
    if (path != NULL) {
        (void)unlink(path);
        free(path);
    }
}
