#include <gabbaboy/gabbaboy.h>

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (file == NULL || fseek(file, 0, SEEK_END) != 0) return 2;
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) return 2;
    uint8_t *rom = malloc((size_t)length);
    if (rom == NULL || fread(rom, 1, (size_t)length, file) != (size_t)length) return 2;
    fclose(file);

    gbb_instance *machine = NULL;
    gbb_error error = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine);
    if (error == GBB_OK) error = gbb_load_rom(machine, rom, (size_t)length);
    free(rom);
    gbb_trace_record *trace = calloc(16384, sizeof(*trace));
    gbb_run_result result = {0};
    if (error == GBB_OK && trace != NULL) result = gbb_run(machine, UINT64_C(200000), trace, 16384);
    int passed = error == GBB_OK && result.reason == GBB_STOP_BUDGET &&
        trace != NULL && result.trace_count > 0 && result.trace_count <= 16384 &&
        gbb_peek_ram(machine, 0xA001) == 0xA5;
    gbb_destroy(machine);
    free(trace);
    if (!passed) fprintf(stderr, "C consumer tracer failed (error=%d, stop=%d)\n", error, result.reason);
    return passed ? 0 : 1;
}
