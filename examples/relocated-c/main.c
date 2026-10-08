#include <gabbaboy/gabbaboy.h>

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <io.h>
#else
#include <unistd.h>
#endif

enum {
    ROM_LIMIT_BYTES = 2 * 1024 * 1024,
    FRAME_WIDTH = 160,
    FRAME_HEIGHT = 144,
    AUDIO_CAPACITY_FRAMES = 4096
};

#define RUN_BUDGET_HALF_DOTS UINT64_C(200000)

static int read_bounded_file(const char *path, uint8_t **out_bytes,
                             size_t *out_size, size_t limit) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return 0;
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return 0;
    }
    long length = ftell(file);
    if (length <= 0 || (unsigned long)length > limit ||
        fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }
    size_t size = (size_t)length;
    uint8_t *bytes = (uint8_t *)malloc(size);
    if (bytes == NULL) {
        fclose(file);
        return 0;
    }
    int ok = fread(bytes, 1, size, file) == size && fgetc(file) == EOF &&
             !ferror(file);
    if (fclose(file) != 0) ok = 0;
    if (!ok) {
        free(bytes);
        return 0;
    }
    *out_bytes = bytes;
    *out_size = size;
    return 1;
}

static int make_temp_path(const char *path, char *out, size_t capacity) {
    unsigned long process_id = 0;
#ifdef _WIN32
    process_id = (unsigned long)GetCurrentProcessId();
#else
    process_id = (unsigned long)getpid();
#endif
    int written = snprintf(out, capacity, "%s.tmp.%lu", path, process_id);
    return written > 0 && (size_t)written < capacity;
}

/* Commit a fully written sibling temp file without truncating the prior save. */
static int replace_save(const char *temp_path, const char *save_path) {
#ifdef _WIN32
    return MoveFileExA(temp_path, save_path,
                       MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    return rename(temp_path, save_path) == 0;
#endif
}

static int write_battery_atomically(const char *save_path,
                                    const uint8_t *bytes, size_t size) {
    char temp_path[4096];
    if (!make_temp_path(save_path, temp_path, sizeof(temp_path))) return 0;
    int descriptor;
#ifdef _WIN32
    descriptor = _open(temp_path, _O_CREAT | _O_EXCL | _O_WRONLY | _O_BINARY,
                       _S_IREAD | _S_IWRITE);
#else
    descriptor = open(temp_path, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW,
                      S_IRUSR | S_IWUSR);
#endif
    if (descriptor < 0) return 0;
#ifdef _WIN32
    FILE *file = _fdopen(descriptor, "wb");
#else
    FILE *file = fdopen(descriptor, "wb");
#endif
    if (file == NULL) {
#ifdef _WIN32
        (void)_close(descriptor);
#else
        (void)close(descriptor);
#endif
        (void)remove(temp_path);
        return 0;
    }
    int ok = fwrite(bytes, 1, size, file) == size && fflush(file) == 0;
#ifdef _WIN32
    if (ok && _commit(_fileno(file)) != 0) ok = 0;
#else
    if (ok && fsync(fileno(file)) != 0) ok = 0;
#endif
    if (fclose(file) != 0) ok = 0;
    if (ok && replace_save(temp_path, save_path)) return 1;
    (void)remove(temp_path);
    return 0;
}

static int load_optional_battery(gbb_instance *machine, const char *save_path,
                                 size_t expected_size) {
    uint8_t *bytes = NULL;
    size_t size = 0;
    if (!read_bounded_file(save_path, &bytes, &size, expected_size)) {
        /* A missing file means a new save; an existing invalid file is an error. */
        FILE *probe = fopen(save_path, "rb");
        if (probe == NULL && errno == ENOENT) return 1;
        if (probe != NULL) fclose(probe);
        return 0;
    }
    int ok = size == expected_size &&
             gbb_import_battery(machine, bytes, size) == GBB_OK;
    free(bytes);
    return ok;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: relocated-c <visible-rom.gb> <battery-rom.gb> <host-save-path>\n");
        return 2;
    }

    uint8_t *rom = NULL;
    size_t rom_size = 0;
    uint8_t *battery_rom = NULL;
    size_t battery_rom_size = 0;
    if (!read_bounded_file(argv[1], &rom, &rom_size, ROM_LIMIT_BYTES) ||
        !read_bounded_file(argv[2], &battery_rom, &battery_rom_size,
                           ROM_LIMIT_BYTES)) {
        fprintf(stderr, "ROM read failed or exceeded the 2 MiB limit\n");
        free(rom);
        free(battery_rom);
        return 1;
    }

    gbb_instance *machine = NULL;
    gbb_error error = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine);
    if (error == GBB_OK) error = gbb_load_rom(machine, rom, rom_size);
    free(rom);
    if (error != GBB_OK) {
        fprintf(stderr, "GabbaBoy create/load failed: %d\n", (int)error);
        gbb_destroy(machine);
        free(battery_rom);
        return 1;
    }

    const gbb_input_event input[] = {
        {8, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {50008, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    error = gbb_queue_events(machine, input, sizeof(input) / sizeof(input[0]));
    if (error != GBB_OK) {
        fprintf(stderr, "timestamped input admission failed: %d\n", (int)error);
        gbb_destroy(machine);
        free(battery_rom);
        return 1;
    }

    gbb_audio_frame audio[AUDIO_CAPACITY_FRAMES];
    size_t audio_count = 0;
    gbb_run_result run = gbb_run_audio(machine, RUN_BUDGET_HALF_DOTS, audio,
                                       AUDIO_CAPACITY_FRAMES, &audio_count);
    if (run.reason != GBB_STOP_BUDGET ||
        run.consumed_half_dots > RUN_BUDGET_HALF_DOTS ||
        audio_count > AUDIO_CAPACITY_FRAMES) {
        fprintf(stderr, "bounded run stopped unexpectedly: reason=%d ticks=%llu audio=%zu\n",
                (int)run.reason, (unsigned long long)run.consumed_half_dots,
                audio_count);
        gbb_destroy(machine);
        free(battery_rom);
        return 1;
    }

    uint8_t pixels[FRAME_WIDTH * FRAME_HEIGHT];
    gbb_frame_info frame_info = {0};
    error = gbb_copy_frame(machine, pixels, sizeof(pixels), FRAME_WIDTH,
                           &frame_info);
    if (error != GBB_OK || frame_info.width != FRAME_WIDTH ||
        frame_info.height != FRAME_HEIGHT) {
        fprintf(stderr, "caller-owned frame copy failed: %d\n", (int)error);
        gbb_destroy(machine);
        free(battery_rom);
        return 1;
    }

    error = gbb_load_rom(machine, battery_rom, battery_rom_size);
    free(battery_rom);
    if (error != GBB_OK) {
        fprintf(stderr, "battery fixture load failed: %d\n", (int)error);
        gbb_destroy(machine);
        return 1;
    }
    size_t battery_size = 0;
    error = gbb_battery_size(machine, &battery_size);
    FILE *saved_file = fopen(argv[3], "rb");
    int resuming = saved_file != NULL;
    if (saved_file != NULL && fclose(saved_file) != 0) {
        fprintf(stderr, "could not close host save file\n");
        gbb_destroy(machine);
        return 1;
    }
    if (error != GBB_OK || battery_size == 0 || battery_size > 32768u ||
        !load_optional_battery(machine, argv[3], battery_size)) {
        fprintf(stderr, "battery import failed or cartridge has no bounded battery RAM\n");
        gbb_destroy(machine);
        return 1;
    }
    gbb_run_result battery_run = gbb_run(machine, RUN_BUDGET_HALF_DOTS, NULL, 0);
    if (battery_run.reason != GBB_STOP_BUDGET ||
        battery_run.consumed_half_dots > RUN_BUDGET_HALF_DOTS ||
        (resuming && gbb_peek_ram(machine, 0xC001u) != 0xA5u) ||
        (!resuming && (gbb_peek_ram(machine, 0xC000u) != 0x01u ||
                       gbb_peek_ram(machine, 0xC002u) != 0xE1u))) {
        fprintf(stderr, "battery continuation fixture did not reach its expected branch\n");
        gbb_destroy(machine);
        return 1;
    }

    uint8_t battery[32768];
    error = gbb_copy_battery(machine, battery, sizeof(battery));
    if (error != GBB_OK ||
        !write_battery_atomically(argv[3], battery, battery_size)) {
        fprintf(stderr, "battery export or atomic host replacement failed: %d\n",
                (int)error);
        gbb_destroy(machine);
        return 1;
    }

    printf("bounded run: %llu/%llu half-dots; frame %ux%u; audio frames %zu; battery bytes %zu\n",
           (unsigned long long)run.consumed_half_dots,
           (unsigned long long)RUN_BUDGET_HALF_DOTS,
           frame_info.width, frame_info.height, audio_count, battery_size);
    gbb_destroy(machine);
    return 0;
}
