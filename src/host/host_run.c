/* Host-mode entry for gabbaboy-runner (Phase 18, D-02..D-04, D-08, D-11).
 *
 * gabbaboy-runner --rom P --save-dir D [--profile dmg|cgb] [--frames N]
 *
 * Headless conformance adapter: load a ROM through a bounded reader, import an exact-size raw
 * `{D}/{stem}.sav`, run fixed frames and publish the battery image with host_save_io_replace.
 * Every refusal exits 2 before the first frame; nothing is ever replaced with fresh cartridge RAM.
 * Diagnostics name reason tokens only, never the caller's --rom or --save-dir path. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

/* ---- Grammar (D-02) ------------------------------------------------------------------------ */

typedef struct {
    const char *rom;
    const char *save_dir;
    gbb_profile profile;
    bool has_frames;
    uint32_t frames;
    bool seen_rom, seen_save_dir, seen_profile, seen_frames;
} host_args;

/* Acceptance-mode flags are named so that mixing them into host mode is a stable, specific refusal
 * rather than a generic unknown flag. */
static const char *const acceptance_flags[] = {
    "--manifest", "--acceptance", "--case", "--suite", "--receipt", "--failure-dir", "--observe",
    "--raw-verdict", "--mutate", "--model", "--revision", "--input-script", "--frame-digest-at",
    "--pcm-digest", "--dump-checkpoints", "--expect-excluded", "--help"
};

bool gbb_host_is_host_invocation(int argc, char **argv) {
    for (int i = 1; i < argc; ++i) {
        const char *a = argv[i];
        if (strcmp(a, "--rom") == 0 || strcmp(a, "--save-dir") == 0 ||
            strncmp(a, "--rom=", 6u) == 0 || strncmp(a, "--save-dir=", 11u) == 0)
            return true;
    }
    return false;
}

/* Plain decimal digits, 1..4294967295. No sign, no whitespace, no base prefix. */
static bool parse_frames(const char *text, uint32_t *out) {
    if (text[0] == '\0') return false;
    uint64_t value = 0u;
    for (const char *p = text; *p != '\0'; ++p) {
        if (*p < '0' || *p > '9') return false;
        value = value * 10u + (uint64_t)(*p - '0');
        if (value > UINT64_C(4294967295)) return false;
    }
    if (value == 0u) return false;
    *out = (uint32_t)value;
    return true;
}

static bool is_acceptance_flag(const char *arg) {
    for (size_t i = 0u; i < sizeof(acceptance_flags) / sizeof(acceptance_flags[0]); ++i)
        if (strcmp(arg, acceptance_flags[i]) == 0) return true;
    return false;
}

/* Returns NULL on success or the grammar reason token of the first defect in argv order. */
static const char *parse_args(int argc, char **argv, host_args *args) {
    memset(args, 0, sizeof(*args));
    args->profile = GBB_PROFILE_DMG_CPU_B;
    for (int i = 1; i < argc; ++i) {
        const char *arg = argv[i];
        if (strncmp(arg, "--", 2u) != 0) return "positional";
        if (strchr(arg, '=') != NULL) return "equals-form";
        bool *seen = NULL;
        if (strcmp(arg, "--rom") == 0) seen = &args->seen_rom;
        else if (strcmp(arg, "--save-dir") == 0) seen = &args->seen_save_dir;
        else if (strcmp(arg, "--profile") == 0) seen = &args->seen_profile;
        else if (strcmp(arg, "--frames") == 0) seen = &args->seen_frames;
        else if (is_acceptance_flag(arg)) return "acceptance-flag";
        else return "unknown-flag";
        if (*seen) return "duplicate-flag";
        *seen = true;
        /* A value that is itself a flag means the real value is missing. */
        if (i + 1 >= argc || strncmp(argv[i + 1], "--", 2u) == 0) return "missing-value";
        const char *value = argv[++i];
        if (value[0] == '\0') return "empty-value";
        if (strcmp(arg, "--rom") == 0) args->rom = value;
        else if (strcmp(arg, "--save-dir") == 0) args->save_dir = value;
        else if (strcmp(arg, "--profile") == 0) {
            if (strcmp(value, "dmg") == 0) args->profile = GBB_PROFILE_DMG_CPU_B;
            else if (strcmp(value, "cgb") == 0) args->profile = GBB_PROFILE_CGB_CPU_E;
            else return "bad-profile";
        } else {
            if (!parse_frames(value, &args->frames)) return "bad-frames";
            args->has_frames = true;
        }
    }
    if (!args->seen_rom) return "missing-rom";
    if (!args->seen_save_dir) return "missing-save-dir";
    return NULL;
}

/* ---- Bounded ROM reader (D-04) ------------------------------------------------------------- */

/* Reads the whole ROM into a fresh allocation. Returns NULL on success or a refusal token.
 * The size is checked against GBB_HOST_MAX_ROM_BYTES before anything is allocated. */
#ifndef _WIN32
static const char *read_rom(const char *path, uint8_t **out, size_t *out_len) {
    /* O_NONBLOCK so a FIFO cannot hang the open; fstat then refuses it before any read. */
    const int fd = open(path, O_RDONLY | O_NONBLOCK | O_NOCTTY | O_CLOEXEC);
    if (fd < 0) return "rom-unreadable";
    struct stat info;
    if (fstat(fd, &info) != 0) { (void)close(fd); return "rom-unreadable"; }
    if (!S_ISREG(info.st_mode)) { (void)close(fd); return "rom-not-regular"; }
    if (info.st_size < 0) { (void)close(fd); return "rom-unreadable"; }
    if ((uintmax_t)info.st_size > (uintmax_t)GBB_HOST_MAX_ROM_BYTES) {
        (void)close(fd);
        return "rom-size";
    }
    const size_t size = (size_t)info.st_size;
    uint8_t *buffer = malloc(size + 1u); /* one spare byte detects a file that grew */
    if (buffer == NULL) { (void)close(fd); return "rom-unreadable"; }
    size_t total = 0u;
    while (total < size + 1u) {
        const ssize_t count = read(fd, buffer + total, size + 1u - total);
        if (count > 0) { total += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { free(buffer); (void)close(fd); return "rom-unreadable"; }
        break;
    }
    (void)close(fd);
    if (total != size) { free(buffer); return "rom-unreadable"; }
    *out = buffer;
    *out_len = size;
    return NULL;
}
#else
/* ISO C only: Windows has no FIFO directory entries and fopen of a directory fails. Binary mode so
 * the CRT never translates CR/LF or stops at a 0x1A byte. */
static const char *read_rom(const char *path, uint8_t **out, size_t *out_len) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return "rom-unreadable";
    if (fseek(file, 0, SEEK_END) != 0) { (void)fclose(file); return "rom-unreadable"; }
    const long length = ftell(file);
    if (length < 0 || fseek(file, 0, SEEK_SET) != 0) { (void)fclose(file); return "rom-unreadable"; }
    if ((unsigned long)length > (unsigned long)GBB_HOST_MAX_ROM_BYTES) {
        (void)fclose(file);
        return "rom-size";
    }
    const size_t size = (size_t)length;
    uint8_t *buffer = malloc(size + 1u);
    if (buffer == NULL) { (void)fclose(file); return "rom-unreadable"; }
    const size_t count = fread(buffer, 1u, size + 1u, file);
    const int failed = ferror(file);
    (void)fclose(file);
    if (failed || count != size) { free(buffer); return "rom-unreadable"; }
    *out = buffer;
    *out_len = size;
    return NULL;
}
#endif

/* ---- Diagnostics --------------------------------------------------------------------------- */

static int refuse(const char *reason) {
    (void)fprintf(stderr, "gbb-host: refused reason=%s\n", reason);
    return 2;
}

static bool host_is_unsupported_platform(void) {
#ifdef _WIN32
    return true;
#else
    return false;
#endif
}

/* ---- The run ------------------------------------------------------------------------------- */

typedef struct {
    int dirfd;
    uint8_t *rom;
    gbb_instance *machine;
    uint8_t *imported; /* the bytes last known to be in the .sav; only meaningful when has_last */
    uint8_t *exported;
} host_run_state;

static void release(host_run_state *state) {
    gbb_destroy(state->machine);
    free(state->rom);
    free(state->imported);
    free(state->exported);
#ifndef _WIN32
    if (state->dirfd >= 0) (void)close(state->dirfd);
#endif
    state->machine = NULL;
    state->rom = state->imported = state->exported = NULL;
    state->dirfd = -1;
}

static int run_host(const host_args *args, const char *stem) {
    host_run_state state = {-1, NULL, NULL, NULL, NULL};
    char sav_name[GBB_HOST_STEM_MAX_BYTES + 8u];
    (void)snprintf(sav_name, sizeof(sav_name), "%s.sav", stem);

    int status = host_save_io_open_dir(args->save_dir, &state.dirfd);
    if (status != HOST_IO_OK)
        return refuse(status == HOST_IO_ENOTDIR ? "save-dir-not-directory" : "save-dir-missing");

    size_t rom_len = 0u;
    const char *rom_reason = read_rom(args->rom, &state.rom, &rom_len);
    if (rom_reason != NULL) { release(&state); return refuse(rom_reason); }

    if (gbb_create(args->profile, &state.machine) != GBB_OK ||
        gbb_load_rom(state.machine, state.rom, rom_len) != GBB_OK) {
        release(&state);
        return refuse("rom-unsupported");
    }
    free(state.rom); /* the core copies what it needs; the file bytes are not kept */
    state.rom = NULL;

    gbb_info info;
    memset(&info, 0, sizeof(info));
    info.struct_size = (uint32_t)sizeof(info);
    if (gbb_get_info(state.machine, &info) != GBB_OK) { release(&state); return refuse("rom-unsupported"); }

    /* Battery carts only: a no-battery cart never opens, reads or creates a .sav (D-08). */
    const bool battery = (info.flags & GBB_INFO_HAS_BATTERY) != 0u;
    size_t want = 0u;
    bool has_last = false; /* false means "none": the .sav is absent and differs from every image */
    if (battery) {
        if (gbb_battery_size(state.machine, &want) != GBB_OK || want > GBB_HOST_MAX_SAVE_BYTES) {
            release(&state);
            return refuse("save-size");
        }
        state.imported = malloc(want + 1u);
        state.exported = malloc(want + 1u);
        if (state.imported == NULL || state.exported == NULL) {
            release(&state);
            return refuse("save-read");
        }
        status = host_save_io_read_exact(state.dirfd, sav_name, state.imported, want);
        if (status == HOST_IO_OK) {
            if (gbb_import_battery(state.machine, state.imported, want) != GBB_OK) {
                release(&state);
                return refuse("save-rtc-block");
            }
            has_last = true;
        } else if (status != HOST_IO_EMISSING) { /* absent is a fresh image; anything else refuses */
            release(&state);
            return refuse(host_io_stage_name(status));
        }
    }

    (void)fprintf(stderr, "gbb-host: ready\n");
    (void)fflush(stderr);

    /* Without --frames the loop runs until the process is killed; pacing and signals arrive later. */
    const uint64_t limit = args->has_frames ? (uint64_t)args->frames : UINT64_MAX;
    uint64_t frame = 0u;
    bool core_stop = false;
    int stop_reason = 0;
    while (frame < limit) {
        const gbb_run_result result = gbb_run(state.machine, GBB_HOST_FRAME_HALF_DOTS, NULL, 0u);
        /* An idle HALT and STOP are normal frames of a quiet guest, not failures. */
        if (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_HALTED_IDLE &&
            result.reason != GBB_STOP_STOPPED) {
            core_stop = true;
            stop_reason = (int)result.reason;
            break;
        }
        ++frame;
    }

    /* Final flush (D-11): write iff the exported image differs from what the .sav last held. */
    const char *flush = "none";
    if (battery) {
        if (gbb_copy_battery(state.machine, state.exported, want) != GBB_OK) {
            (void)fprintf(stderr, "gbb-host: flush reason=final frame=%llu result=failed stage=export\n",
                          (unsigned long long)frame);
            release(&state);
            return 1;
        }
        if (!has_last || memcmp(state.exported, state.imported, want) != 0) {
            status = host_save_io_replace(state.dirfd, sav_name, state.exported, want);
            if (status != HOST_IO_OK) {
                (void)fprintf(stderr,
                              "gbb-host: flush reason=final frame=%llu result=failed stage=%s\n",
                              (unsigned long long)frame, host_io_stage_name(status));
                release(&state);
                return 1;
            }
            memcpy(state.imported, state.exported, want);
            has_last = true;
            flush = "written";
        } else {
            flush = "unchanged";
        }
        (void)fprintf(stderr, "gbb-host: flush reason=final frame=%llu result=%s\n",
                      (unsigned long long)frame, flush);
    }

    if (core_stop) {
        (void)fprintf(stderr, "gbb-host: exit status=core-stop reason=%d stopped_at_frame=%llu flush=%s\n",
                      stop_reason, (unsigned long long)frame, flush);
        release(&state);
        return 1;
    }
    (void)fprintf(stderr, "gbb-host: exit status=clean reason=frames stopped_at_frame=%llu flush=%s\n",
                  (unsigned long long)frame, flush);
    release(&state);
    return 0;
}

int gbb_host_main(int argc, char **argv) {
    host_args args;
    const char *reason = parse_args(argc, argv, &args);
    if (reason != NULL) {
        (void)fprintf(stderr, "invalid-arguments: reason=%s\n", reason);
        return 2;
    }
    if (host_is_unsupported_platform()) return refuse("windows-unsupported"); /* D-05 */

    char stem[GBB_HOST_STEM_MAX_BYTES + 1u];
    const host_stem_status stem_status = host_stem(args.rom, stem, sizeof(stem));
    if (stem_status != HOST_STEM_OK) return refuse(host_stem_reason(stem_status));
    return run_host(&args, stem);
}
