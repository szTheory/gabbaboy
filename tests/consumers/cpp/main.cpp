#include <gabbaboy/gabbaboy.h>

#include <cstdio>
#include <cstdlib>

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
    auto *trace = static_cast<gbb_trace_record *>(std::calloc(16384, sizeof(gbb_trace_record)));
    gbb_run_result result{};
    if (error == GBB_OK && trace != nullptr) result = gbb_run(machine, UINT64_C(200000), trace, 16384);
    bool passed = error == GBB_OK && result.reason == GBB_STOP_BUDGET &&
        trace != nullptr && result.trace_count > 0 && result.trace_count <= 16384 &&
        gbb_peek_ram(machine, 0xA001) == 0xA5;
    gbb_destroy(machine);
    std::free(trace);
    if (!passed) std::fprintf(stderr, "C++ consumer tracer failed (error=%d, stop=%d)\n", error, result.reason);
    return passed ? 0 : 1;
}
