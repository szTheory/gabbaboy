#include <gabbaboy/gabbaboy.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

static int battery_api_smoke() {
    constexpr size_t rom_bytes = 32768u;
    constexpr size_t ram_bytes = 8192u;
    uint8_t rom[rom_bytes]{};
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = static_cast<uint8_t>(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;

    gbb_instance *machine = nullptr;
    uint8_t input[ram_bytes]{};
    uint8_t output[ram_bytes + 2u]{};
    size_t size = 0u;
    uint64_t generation = 0u;
    bool passed = false;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) goto done;
    if (gbb_battery_size(machine, &size) != GBB_OK || size != ram_bytes) goto done;
    std::memset(output, 0xA7, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, ram_bytes - 1u) !=
        GBB_BUFFER_TOO_SMALL) goto done;
    for (size_t i = 0u; i < sizeof(output); ++i)
        if (output[i] != 0xA7u) goto done;
    if (gbb_copy_battery(machine, output + 1u, ram_bytes) != GBB_OK) goto done;
    for (size_t i = 0u; i < ram_bytes; ++i)
        if (output[i + 1u] != 0xFFu) goto done;
    if (output[0] != 0xA7u || output[sizeof(output) - 1u] != 0xA7u) goto done;

    for (size_t i = 0u; i < ram_bytes; ++i)
        input[i] = static_cast<uint8_t>(i * 37u + 0x31u);
    if (gbb_import_battery(machine, input, sizeof(input)) != GBB_OK) goto done;
    if (gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    if (gbb_import_battery(machine, input, sizeof(input) - 1u) !=
        GBB_BATTERY_SIZE_MISMATCH) goto done;
    std::memset(output, 0x5C, sizeof(output));
    if (gbb_copy_battery(machine, output + 1u, ram_bytes) != GBB_OK ||
        std::memcmp(output + 1u, input, sizeof(input)) != 0 ||
        output[0] != 0x5Cu || output[sizeof(output) - 1u] != 0x5Cu ||
        gbb_battery_generation(machine, &generation) != GBB_OK || generation != 1u)
        goto done;
    passed = true;

done:
    gbb_destroy(machine);
    return passed ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = std::fopen(argv[1], "rb");
    if (file == nullptr || std::fseek(file, 0, SEEK_END) != 0) return 2;
    long length = std::ftell(file);
    if (length <= 0 || std::fseek(file, 0, SEEK_SET) != 0) return 2;
    auto *rom = static_cast<uint8_t *>(std::malloc(static_cast<size_t>(length)));
    if (rom == nullptr || std::fread(rom, 1, static_cast<size_t>(length), file) != static_cast<size_t>(length)) return 2;
    std::fclose(file);

    gbb_instance *machine = nullptr;
    gbb_error error = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine);
    if (error == GBB_OK) error = gbb_load_rom(machine, rom, static_cast<size_t>(length));
    std::free(rom);
    gbb_input_event events[64]{};
    for (size_t i = 0; i < 64; ++i) {
        events[i].at_half_dots = i;
        events[i].kind = GBB_INPUT_STOP_WAKE;
        events[i].value = 1;
    }
    events[62] = {62, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    events[63] = {63, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A};
    gbb_error event_error = error == GBB_OK ? gbb_queue_events(machine, events, 64) : error;
    gbb_input_event excess{64, static_cast<gbb_input_event_kind>(99), 0};
    gbb_error capacity_error = event_error == GBB_OK ? gbb_queue_events(machine, &excess, 1) : event_error;
    auto *trace = static_cast<gbb_trace_record *>(std::calloc(16384, sizeof(gbb_trace_record)));
    auto *diagnostics = static_cast<gbb_diagnostic_record *>(std::calloc(16384, sizeof(gbb_diagnostic_record)));
    gbb_run_result result{};
    if (error == GBB_OK && event_error == GBB_OK && trace != nullptr && diagnostics != nullptr)
        result = gbb_run_ex(machine, UINT64_C(160000), trace, 16384, diagnostics, 16384);
    bool chronological = true;
    for (size_t i = 1; i < result.diagnostic_count; ++i)
        if (diagnostics[i - 1].time_half_dots > diagnostics[i].time_half_dots) chronological = false;
    uint8_t frame[160u * 144u]{};
    gbb_frame_info frame_info{};
    gbb_error frame_error = error == GBB_OK
        ? gbb_copy_frame(machine, frame, sizeof(frame), 160, &frame_info) : error;
    bool shades_valid = true;
    if (frame_error == GBB_OK)
        for (uint8_t shade : frame)
            if (shade > 3u) shades_valid = false;
    bool passed = error == GBB_OK && event_error == GBB_OK && capacity_error == GBB_EVENT_QUEUE_FULL &&
        result.reason == GBB_STOP_BUDGET && result.consumed_half_dots <= UINT64_C(160000) &&
        trace != nullptr && result.trace_count > 0 && result.trace_count <= 16384 &&
        diagnostics != nullptr && result.diagnostic_count > 0 && result.diagnostic_count <= 16384 && chronological &&
        gbb_peek_ram(machine, 0xC001) == 0xA5 && frame_error == GBB_OK &&
        frame_info.width == 160 && frame_info.height == 144 && frame_info.generation > 0 && shades_valid;
    gbb_destroy(machine);
    std::free(trace);
    std::free(diagnostics);
    if (!passed) std::fprintf(stderr, "C++ consumer API smoke failed (error=%d, stop=%d, frame=%d)\n", error, result.reason, frame_error);
    if (!passed || battery_api_smoke() != 0) {
        std::fprintf(stderr, "C++ consumer public battery API smoke failed\n");
        return 1;
    }
    return 0;
}
