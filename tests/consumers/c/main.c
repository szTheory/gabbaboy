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
    gbb_input_event events[64];
    for (size_t i = 0; i < 64; ++i) {
        events[i].at_half_dots = i;
        events[i].kind = GBB_INPUT_STOP_WAKE;
        events[i].value = 1;
    }
    gbb_error event_error = error == GBB_OK ? gbb_queue_events(machine, events, 64) : error;
    gbb_input_event excess = {64, GBB_INPUT_STOP_WAKE, 1};
    gbb_error capacity_error = event_error == GBB_OK ? gbb_queue_events(machine, &excess, 1) : event_error;
    gbb_trace_record *trace = calloc(16384, sizeof(*trace));
    gbb_diagnostic_record *diagnostics = calloc(16384, sizeof(*diagnostics));
    gbb_run_result result = {0};
    if (error == GBB_OK && event_error == GBB_OK && trace != NULL && diagnostics != NULL)
        result = gbb_run_ex(machine, UINT64_C(200000), trace, 16384, diagnostics, 16384);
    int chronological = 1;
    for (size_t i = 1; i < result.diagnostic_count; ++i)
        if (diagnostics[i - 1].time_half_dots > diagnostics[i].time_half_dots) chronological = 0;
    int passed = error == GBB_OK && event_error == GBB_OK && capacity_error == GBB_EVENT_QUEUE_FULL &&
        result.reason == GBB_STOP_BUDGET && result.consumed_half_dots <= UINT64_C(200000) &&
        trace != NULL && result.trace_count > 0 && result.trace_count <= 16384 &&
        diagnostics != NULL && result.diagnostic_count > 0 && result.diagnostic_count <= 16384 && chronological &&
        gbb_peek_ram(machine, 0xC001) == 0xA5;
    gbb_destroy(machine);
    free(trace);
    free(diagnostics);
    if (!passed) fprintf(stderr, "C consumer tracer failed (error=%d, stop=%d)\n", error, result.reason);
    return passed ? 0 : 1;
}
