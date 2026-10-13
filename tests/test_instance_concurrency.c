#include "gabbaboy/gabbaboy.h"

#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
typedef HANDLE test_thread;
#else
#include <pthread.h>
typedef pthread_t test_thread;
#endif

extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);

typedef struct {
    gbb_instance *instance;
    atomic_int *ready;
    atomic_int *start;
    uint8_t expected_ram_value;
    int passed;
} worker_args;

static void *run_repeatedly(void *opaque) {
    worker_args *args = (worker_args *)opaque;
    atomic_fetch_add_explicit(args->ready, 1, memory_order_release);
    while (atomic_load_explicit(args->start, memory_order_acquire) == 0) { }

    args->passed = 1;
    for (int i = 0; i < 100; ++i) {
        gbb_run_result result;
        if (gbb_reset(args->instance) != GBB_OK) { args->passed = 0; break; }
        result = gbb_run(args->instance, 88, NULL, 0);
        if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots != 88 ||
            gbb_peek_ram(args->instance, 0xC000) != args->expected_ram_value) {
            args->passed = 0;
            break;
        }
    }
    return NULL;
}

#ifdef _WIN32
static DWORD WINAPI windows_worker(LPVOID opaque) {
    (void)run_repeatedly(opaque);
    return 0;
}
#endif

/* cgb_instance_isolation (Plan 10-18, CGB-02): a CGB instance, which owns its own bank state and
 * decode tables, must not disturb a DMG instance. The DMG tracer is run alone and its trace digest
 * recorded; the same DMG run alongside a CGB instance, interleaved on one thread and then with the
 * CGB instance on a second thread, must reproduce that digest exactly. */
#define ISO_SLICES 64u
#define ISO_SLICE_HALF_DOTS 512u
#define ISO_TRACE 64u

static uint64_t fnv_u64(uint64_t hash, uint64_t value) {
    for (int i = 0; i < 8; ++i) {
        hash ^= (value >> (8 * i)) & 0xFFu;
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint64_t run_slice_digest(gbb_instance *m, uint64_t hash) {
    gbb_trace_record trace[ISO_TRACE];
    const gbb_run_result r = gbb_run(m, ISO_SLICE_HALF_DOTS, trace, ISO_TRACE);
    hash = fnv_u64(hash, r.consumed_half_dots);
    hash = fnv_u64(hash, (uint64_t)r.reason);
    hash = fnv_u64(hash, r.trace_count);
    for (size_t i = 0u; i < r.trace_count && i < ISO_TRACE; ++i) {   /* field by field, no padding */
        hash = fnv_u64(hash, trace[i].time_half_dots);
        hash = fnv_u64(hash, trace[i].pc);
        hash = fnv_u64(hash, ((uint64_t)trace[i].a << 8) | trace[i].f);
        hash = fnv_u64(hash, ((uint64_t)trace[i].b << 8) | trace[i].c);
        hash = fnv_u64(hash, ((uint64_t)trace[i].d << 8) | trace[i].e);
        hash = fnv_u64(hash, ((uint64_t)trace[i].h << 8) | trace[i].l);
        hash = fnv_u64(hash, trace[i].sp);
    }
    return fnv_u64(hash, gbb_peek_ram(m, 0xC000u));
}

typedef struct {
    gbb_instance *instance;
    atomic_int *ready;
    atomic_int *start;
    uint64_t digest;
} iso_args;

static void *iso_worker(void *opaque) {
    iso_args *args = (iso_args *)opaque;
    atomic_fetch_add_explicit(args->ready, 1, memory_order_release);
    while (atomic_load_explicit(args->start, memory_order_acquire) == 0) { }
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned i = 0u; i < ISO_SLICES; ++i) hash = run_slice_digest(args->instance, hash);
    args->digest = hash;
    return NULL;
}

#ifdef _WIN32
static DWORD WINAPI iso_windows_worker(LPVOID opaque) {
    (void)iso_worker(opaque);
    return 0;
}
#endif

static void fix_header_checksum(uint8_t *rom) {
    uint8_t sum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14Du] = sum;
}

static int cgb_instance_isolation(const char *path) {
    FILE *file = fopen(path, "rb");
    static uint8_t tracer[32768];
    static uint8_t noise[32768];
    if (!file || fread(tracer, 1, sizeof(tracer), file) != sizeof(tracer)) return 2;
    fclose(file);
    /* The CGB neighbour hammers VBK and SVBK so any shared bank state would leak. */
    noise[0x100] = 0xC3u; noise[0x101] = 0x50u; noise[0x102] = 0x01u;
    static const uint8_t loop[] = {0x3Eu, 0x01u, 0xE0u, 0x4Fu, 0x3Eu, 0x07u, 0xE0u, 0x70u,
                                   0xAF, 0xE0u, 0x4Fu, 0x3Eu, 0x03u, 0xE0u, 0x70u, 0x18u, 0xF1u};
    memcpy(noise + 0x150, loop, sizeof(loop));
    noise[0x143] = 0x80u;
    fix_header_checksum(noise);

    gbb_instance *alone = NULL, *dmg = NULL, *cgb = NULL, *dmg2 = NULL, *cgb2 = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &alone) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &dmg) != GBB_OK ||
        gbb_create(GBB_PROFILE_CGB_CPU_E, &cgb) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &dmg2) != GBB_OK ||
        gbb_create(GBB_PROFILE_CGB_CPU_E, &cgb2) != GBB_OK ||
        gbb_load_rom(alone, tracer, sizeof(tracer)) != GBB_OK ||
        gbb_load_rom(dmg, tracer, sizeof(tracer)) != GBB_OK ||
        gbb_load_rom(dmg2, tracer, sizeof(tracer)) != GBB_OK ||
        gbb_load_rom(cgb, noise, sizeof(noise)) != GBB_OK ||
        gbb_load_rom(cgb2, noise, sizeof(noise)) != GBB_OK) return 1;

    uint64_t alone_digest = UINT64_C(14695981039346656037);
    for (unsigned i = 0u; i < ISO_SLICES; ++i) alone_digest = run_slice_digest(alone, alone_digest);

    /* One thread, interleaved slice by slice. */
    uint64_t mixed = UINT64_C(14695981039346656037);
    uint64_t cgb_hash = 0u;
    for (unsigned i = 0u; i < ISO_SLICES; ++i) {
        cgb_hash = run_slice_digest(cgb, cgb_hash);
        mixed = run_slice_digest(dmg, mixed);
    }

    /* Two threads: the DMG instance on one, the CGB neighbour on the other. */
    atomic_int ready = 0;
    atomic_int start = 0;
    iso_args args[2] = {{dmg2, &ready, &start, 0u}, {cgb2, &ready, &start, 0u}};
    test_thread threads[2];
#ifdef _WIN32
    threads[0] = CreateThread(NULL, 0, iso_windows_worker, &args[0], 0, NULL);
    threads[1] = CreateThread(NULL, 0, iso_windows_worker, &args[1], 0, NULL);
    if (!threads[0] || !threads[1]) return 2;
#else
    if (pthread_create(&threads[0], NULL, iso_worker, &args[0]) != 0) return 2;
    if (pthread_create(&threads[1], NULL, iso_worker, &args[1]) != 0) {
        atomic_store_explicit(&start, 1, memory_order_release);
        pthread_join(threads[0], NULL);
        return 2;
    }
#endif
    while (atomic_load_explicit(&ready, memory_order_acquire) != 2) { }
    atomic_store_explicit(&start, 1, memory_order_release);
#ifdef _WIN32
    WaitForMultipleObjects(2, threads, TRUE, INFINITE);
    CloseHandle(threads[0]);
    CloseHandle(threads[1]);
#else
    pthread_join(threads[0], NULL);
    pthread_join(threads[1], NULL);
#endif

    /* The neighbour really ran and changed its own banks, and a different guest digests
     * differently, so equal DMG digests are not an artefact of a dead comparison. */
    uint8_t vram_bank = 0u, wram_bank = 0u;
    gbb_test_bank_state(cgb, &vram_bank, &wram_bank);
    uint8_t dmg_vram = 9u, dmg_wram = 9u;
    gbb_test_bank_state(dmg, &dmg_vram, &dmg_wram);
    int ok = mixed == alone_digest && args[0].digest == alone_digest &&
             vram_bank <= 1u && wram_bank >= 1u && wram_bank <= 7u &&
             (vram_bank != 0u || wram_bank != 1u) &&
             dmg_vram == 0u && dmg_wram == 1u && cgb_hash != alone_digest &&
             args[1].digest != alone_digest;
    if (!ok)
        fprintf(stderr, "isolation: alone=%016llx mixed=%016llx threaded=%016llx cgb banks=%u/%u\n",
                (unsigned long long)alone_digest, (unsigned long long)mixed,
                (unsigned long long)args[0].digest, vram_bank, wram_bank);
    /* Negative control: a differing guest must change the digest. */
    tracer[0x154] ^= 0xFFu;
    gbb_instance *other = NULL;
    uint64_t other_digest = UINT64_C(14695981039346656037);
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &other) != GBB_OK ||
        gbb_load_rom(other, tracer, sizeof(tracer)) != GBB_OK) ok = 0;
    else {
        for (unsigned i = 0u; i < ISO_SLICES; ++i) other_digest = run_slice_digest(other, other_digest);
        if (other_digest == alone_digest) { fprintf(stderr, "digest control insensitive\n"); ok = 0; }
    }
    gbb_destroy(other);
    gbb_destroy(alone); gbb_destroy(dmg); gbb_destroy(cgb); gbb_destroy(dmg2); gbb_destroy(cgb2);
    return ok ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[2], "cgb_instance_isolation") == 0)
        return cgb_instance_isolation(argv[1]);
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file || fseek(file, 0, SEEK_END) != 0) return 2;
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET) != 0) return 2;
    uint8_t *rom[2] = {
        (uint8_t *)malloc((size_t)length),
        (uint8_t *)malloc((size_t)length)
    };
    if (!rom[0] || !rom[1] || fread(rom[0], 1, (size_t)length, file) != (size_t)length) return 2;
    fclose(file);
    memcpy(rom[1], rom[0], (size_t)length);

    /* Change the second fixture's write and compare immediates outside the header. */
    if ((size_t)length <= 0x158u) return 2;
    rom[1][0x154] = 0xA5;
    rom[1][0x158] = 0xA5;

    gbb_instance *instances[2] = {NULL, NULL};
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &instances[0]) != GBB_OK ||
        gbb_create(GBB_PROFILE_DMG_CPU_B, &instances[1]) != GBB_OK ||
        gbb_load_rom(instances[0], rom[0], (size_t)length) != GBB_OK ||
        gbb_load_rom(instances[1], rom[1], (size_t)length) != GBB_OK) return 1;
    free(rom[0]);
    free(rom[1]);

    atomic_int ready = 0;
    atomic_int start = 0;
    worker_args args[2] = {
        {instances[0], &ready, &start, 0x5A, 0},
        {instances[1], &ready, &start, 0xA5, 0}
    };
    test_thread threads[2];
#ifdef _WIN32
    threads[0] = CreateThread(NULL, 0, windows_worker, &args[0], 0, NULL);
    if (!threads[0]) {
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
    threads[1] = CreateThread(NULL, 0, windows_worker, &args[1], 0, NULL);
    if (!threads[1]) {
        atomic_store_explicit(&start, 1, memory_order_release);
        WaitForSingleObject(threads[0], INFINITE);
        CloseHandle(threads[0]);
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
#else
    if (pthread_create(&threads[0], NULL, run_repeatedly, &args[0]) != 0) {
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
    if (pthread_create(&threads[1], NULL, run_repeatedly, &args[1]) != 0) {
        atomic_store_explicit(&start, 1, memory_order_release);
        pthread_join(threads[0], NULL);
        gbb_destroy(instances[0]);
        gbb_destroy(instances[1]);
        return 2;
    }
#endif
    while (atomic_load_explicit(&ready, memory_order_acquire) != 2) { }
    atomic_store_explicit(&start, 1, memory_order_release);
#ifdef _WIN32
    WaitForMultipleObjects(2, threads, TRUE, INFINITE);
    CloseHandle(threads[0]);
    CloseHandle(threads[1]);
#else
    pthread_join(threads[0], NULL);
    pthread_join(threads[1], NULL);
#endif
    gbb_destroy(instances[0]);
    gbb_destroy(instances[1]);
    if (!args[0].passed || !args[1].passed) {
        fprintf(stderr, "concurrent independent instance run diverged\n");
        return 1;
    }
    return 0;
}
