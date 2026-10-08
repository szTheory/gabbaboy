#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gabbaboy/gabbaboy.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#endif

#define WORKLOAD_HALF_DOTS UINT64_C(1000000)
#define MAX_ROM_BYTES 32768u
#define TRACE_CAPACITY 65536u

static uint64_t digest_byte(uint64_t hash, uint8_t value) {
    return (hash ^ value) * UINT64_C(1099511628211);
}

static int read_rom(const char *path, uint8_t rom[MAX_ROM_BYTES], size_t *size) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return 0;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return 0; }
    long length = ftell(file);
    if (length <= 0 || (unsigned long)length > MAX_ROM_BYTES ||
        fseek(file, 0, SEEK_SET) != 0) { fclose(file); return 0; }
    *size = (size_t)length;
    int ok = fread(rom, 1, *size, file) == *size;
    if (fclose(file) != 0) ok = 0;
    return ok;
}

static uint64_t guest_digest(const gbb_instance *machine) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (uint32_t address = 0xc000; address <= 0xdfff; ++address)
        hash = digest_byte(hash, gbb_peek_ram(machine, (uint16_t)address));
    for (uint32_t address = 0xff80; address <= 0xfffe; ++address)
        hash = digest_byte(hash, gbb_peek_ram(machine, (uint16_t)address));
    return hash;
}

static int monotonic_now(struct timespec *value) {
#ifdef _WIN32
    LARGE_INTEGER counter, frequency;
    if (!QueryPerformanceFrequency(&frequency) || !QueryPerformanceCounter(&counter)) return 0;
    value->tv_sec = (time_t)(counter.QuadPart / frequency.QuadPart);
    value->tv_nsec = (long)(((counter.QuadPart % frequency.QuadPart) * INT64_C(1000000000)) /
                            frequency.QuadPart);
    return 1;
#else
    return clock_gettime(CLOCK_MONOTONIC, value) == 0;
#endif
}

static long monotonic_resolution_ns(void) {
#ifdef _WIN32
    LARGE_INTEGER frequency;
    if (!QueryPerformanceFrequency(&frequency) || frequency.QuadPart <= 0) return 0;
    return (long)((INT64_C(1000000000) + frequency.QuadPart - 1) / frequency.QuadPart);
#else
    struct timespec resolution;
    if (clock_getres(CLOCK_MONOTONIC, &resolution) != 0) return 0;
    return (long)(resolution.tv_sec * 1000000000L + resolution.tv_nsec);
#endif
}

static uint64_t peak_rss_bytes(void) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS counters;
    counters.cb = sizeof(counters);
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof(counters))) return 0;
    return (uint64_t)counters.PeakWorkingSetSize;
#else
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) != 0 || usage.ru_maxrss <= 0) return 0;
#ifdef __APPLE__
    return (uint64_t)usage.ru_maxrss;
#else
    return (uint64_t)usage.ru_maxrss * UINT64_C(1024);
#endif
#endif
}

int main(int argc, char **argv) {
    if (argc != 3 || (strcmp(argv[1], "--trace") != 0 &&
                      strcmp(argv[1], "--no-trace") != 0)) {
        fprintf(stderr, "usage: measure_core (--trace|--no-trace) <rom>\n");
        return 2;
    }
    const int trace_enabled = strcmp(argv[1], "--trace") == 0;
    uint8_t rom[MAX_ROM_BYTES];
    size_t rom_size = 0;
    if (!read_rom(argv[2], rom, &rom_size)) {
        fprintf(stderr, "measurement ROM missing, oversized, or unreadable\n");
        return 2;
    }
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, rom_size) != GBB_OK) {
        gbb_destroy(machine);
        fprintf(stderr, "measurement ROM rejected by the DMG-CPU-B profile\n");
        return 2;
    }
    gbb_trace_record *trace = NULL;
    if (trace_enabled) {
        trace = calloc(TRACE_CAPACITY, sizeof(*trace));
        if (trace == NULL) { gbb_destroy(machine); return 2; }
    }
    struct timespec start, finish;
    if (!monotonic_now(&start)) {
        free(trace); gbb_destroy(machine); return 2;
    }
    gbb_run_result result = gbb_run(machine, WORKLOAD_HALF_DOTS, trace,
                                    trace_enabled ? TRACE_CAPACITY : 0);
    if (!monotonic_now(&finish)) {
        free(trace); gbb_destroy(machine); return 2;
    }
    const int64_t elapsed_ns = (int64_t)(finish.tv_sec - start.tv_sec) * INT64_C(1000000000) +
                               (int64_t)finish.tv_nsec - start.tv_nsec;
    const uint64_t digest = guest_digest(machine);
    const uint64_t rss_bytes = peak_rss_bytes();
    const long clock_resolution = monotonic_resolution_ns();
    printf("mode=%s workload=original-wram-tracer-1m-half-dots-v1 budget_half_dots=%" PRIu64
           " consumed_half_dots=%" PRIu64 " stop_reason=%u elapsed_ns=%" PRId64
           " clock_resolution_ns=%ld clock_method=monotonic peak_rss_bytes=%" PRIu64
           " trace_records=%zu correctness_digest_fnv1a64=%016" PRIx64 "\n",
           trace_enabled ? "trace" : "no-trace", WORKLOAD_HALF_DOTS,
           result.consumed_half_dots, (unsigned)result.reason, elapsed_ns, clock_resolution, rss_bytes,
           result.trace_count, digest);
    free(trace);
    gbb_destroy(machine);
    return result.reason == GBB_STOP_BUDGET && result.consumed_half_dots > 0 &&
           result.consumed_half_dots <= WORKLOAD_HALF_DOTS &&
           (!trace_enabled || result.trace_count <= TRACE_CAPACITY) && elapsed_ns > 0 &&
           clock_resolution > 0 && rss_bytes > 0 ? 0 : 1;
}
