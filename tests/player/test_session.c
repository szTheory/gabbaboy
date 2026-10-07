#include "session.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    rom[0x147] = 1;
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
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       error, sizeof(error)));
    REQUIRE(strcmp(current_path, demo_path) == 0);
    REQUIRE(run_visible_press(machine) == 0);

    const char *const original_path = current_path;
    uint8_t pixels[160 * 144];
    gbb_frame_info before;
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), 160, &before) == GBB_OK);
    REQUIRE(write_truncated_file(missing_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        error, sizeof(error)));
    REQUIRE(strstr(error, "truncated") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);
    gbb_frame_info after;
    REQUIRE(gbb_copy_frame(machine, pixels, sizeof(pixels), 160, &after) == GBB_OK);
    REQUIRE(after.generation == before.generation &&
            after.completion_half_dots == before.completion_half_dots);

    (void)remove(missing_path);
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        error, sizeof(error)));
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    REQUIRE(write_oversized_file(missing_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        error, sizeof(error)));
    REQUIRE(strstr(error, "32 KiB") != NULL);
    REQUIRE(require_unchanged(machine, current_path, original_path, error) == 0);

    REQUIRE(write_unsupported_cartridge(missing_path, demo_path));
    REQUIRE(!player_session_replace_rom(machine, &current_path, missing_path,
                                        error, sizeof(error)));
    REQUIRE(strstr(error, "ROM-only") != NULL);
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
    char error[256];
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       error, sizeof(error)));
    REQUIRE(run_visible_press(machine) == 0);
    REQUIRE(player_session_replace_rom(machine, &current_path, demo_path,
                                       error, sizeof(error)));
    REQUIRE(strcmp(current_path, demo_path) == 0 && error[0] == '\0');
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 0 && gbb_peek_ram(machine, 0xC001) == 0);
    free(current_path);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    if (strcmp(argv[1], "player_session_replacement_failure") == 0)
        return replacement_failure(argv[2], argv[3]);
    if (strcmp(argv[1], "player_session_replacement_success") == 0)
        return replacement_success(argv[2]);
    return 2;
}
