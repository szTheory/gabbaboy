#include "session.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PLAYER_SESSION_ROM_SIZE 32768u

static void set_error(char *out_error, size_t capacity, const char *message) {
    if (out_error == NULL || capacity == 0) return;
    (void)snprintf(out_error, capacity, "%s", message);
}

static const char *rom_error(gbb_error error) {
    switch (error) {
    case GBB_ROM_TRUNCATED:
        return "The selected file is truncated; choose an exact 32 KiB ROM-only image.";
    case GBB_ROM_TOO_LARGE:
        return "The selected file exceeds the supported 32 KiB ROM-only size.";
    case GBB_ROM_SIZE_MISMATCH:
        return "The selected ROM must be exactly 32 KiB.";
    case GBB_UNSUPPORTED_CARTRIDGE:
        return "Only ROM-only cartridges are supported.";
    case GBB_UNSUPPORTED_ROM_SIZE:
        return "Only 32 KiB ROM-only images are supported.";
    case GBB_UNSUPPORTED_RAM_SIZE:
        return "Cartridge RAM is unsupported; choose a ROM-only image with no RAM.";
    case GBB_INVALID_ROM:
        return "The ROM header checksum is invalid.";
    case GBB_OUT_OF_MEMORY:
        return "There is not enough memory to load this ROM.";
    default:
        return "The selected file is not a supported 32 KiB ROM-only image.";
    }
}

static bool copy_rom_path(const char *path, char **out_copy,
                          char *out_error, size_t error_capacity) {
    if (path == NULL || path[0] == '\0') {
        set_error(out_error, error_capacity, "No ROM file was selected.");
        return false;
    }
    size_t length = 0;
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

static bool read_rom_file(const char *path, uint8_t rom[PLAYER_SESSION_ROM_SIZE],
                          size_t *out_size, char *out_error,
                          size_t error_capacity) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        const int saved_errno = errno;
        char message[256];
        (void)snprintf(message, sizeof(message), "Could not open the selected ROM: %s",
                       strerror(saved_errno));
        set_error(out_error, error_capacity, message);
        return false;
    }

    uint8_t bytes[PLAYER_SESSION_ROM_SIZE + 1u];
    const size_t count = fread(bytes, 1, sizeof(bytes), file);
    const bool read_failed = ferror(file) != 0;
    const int close_result = fclose(file);
    if (read_failed || close_result != 0) {
        set_error(out_error, error_capacity, "Could not read the selected ROM completely.");
        return false;
    }
    if (count > PLAYER_SESSION_ROM_SIZE) {
        set_error(out_error, error_capacity,
                  "The selected file exceeds 32 KiB; only exact 32 KiB ROM-only images are supported.");
        return false;
    }
    memcpy(rom, bytes, count);
    *out_size = count;
    return true;
}

bool player_session_replace_rom(gbb_instance *machine, char **in_out_path,
                                const char *path, char *out_error,
                                size_t error_capacity) {
    if (out_error != NULL && error_capacity > 0) out_error[0] = '\0';
    if (machine == NULL || in_out_path == NULL) {
        set_error(out_error, error_capacity, "The player session is unavailable.");
        return false;
    }

    char *new_path = NULL;
    if (!copy_rom_path(path, &new_path, out_error, error_capacity)) return false;

    uint8_t rom[PLAYER_SESSION_ROM_SIZE];
    size_t rom_size = 0;
    if (!read_rom_file(path, rom, &rom_size, out_error, error_capacity)) {
        free(new_path);
        return false;
    }

    const gbb_error result = gbb_load_rom(machine, rom, rom_size);
    if (result != GBB_OK) {
        set_error(out_error, error_capacity, rom_error(result));
        free(new_path);
        return false;
    }

    free(*in_out_path);
    *in_out_path = new_path;
    return true;
}
